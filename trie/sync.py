import bisect

from eth_utils import (
    encode_hex,
    keccak,
)

from trie.constants import (
    NODE_TYPE_BRANCH,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_LEAF,
)
from trie.exceptions import (
    SyncRequestAlreadyProcessed,
    UnexpectedNodeType,
)
from trie.utils.nodes import (
    decode_node,
    get_node_type,
    is_blank_node,
)


class SyncRequest:

    def __init__(self, node_key, parent, depth, leaf_callback, is_raw=False):
        """Create a new SyncRequest for a given HexaryTrie node.

        :param node_key: The node's key.
        :param parent: The node's parent.
        :param depth: The ndoe's depth in the trie.
        :param leaf_callback: A callback called when for all leaf children of this node.
        :param is_raw: If True, HexaryTrieSync will simply store the node's data in the db,
        without decoding and scheduling requests for children. This is needed to fetch contract
        code when doing a state sync.
        """
        self.node_key = node_key
        self.parents = []
        if parent is not None:
            self.parents = [parent]
        self.depth = depth
        self.leaf_callback = leaf_callback
        self.is_raw = is_raw
        self.dependencies = 0
        self.data = None

    def __lt__(self, other):
        return self.depth < other.depth

    def __repr__(self):
        return "SyncRequest(%s, depth=%d)" % (encode_hex(self.node_key), self.depth)


class HexaryTrieSync:

    def __init__(self, root_hash, db, logger):
        self.queue = []
        self.requests = {}
        self.db = db
        self.root_hash = root_hash
        self.logger = logger
        self.schedule(root_hash, parent=None, depth=0, leaf_callback=self.leaf_callback)

    def leaf_callback(self, data, parent):
        """Called when we reach a leaf node.

        Should be implemented by subclasses that need to perform special handling of leaves.
        """
        pass

    @property
    def has_pending_requests(self):
        return len(self.requests) > 0

    def next_batch(self, n=1):
        """Return the next requests that should be dispatched."""
        if len(self.queue) == 0:
            return []
        batch = list(reversed((self.queue[-n:])))
        self.queue = self.queue[:-n]
        return batch

    def schedule(self, node_key, parent, depth, leaf_callback, is_raw=False):
        """Schedule a request for the node with the given key."""
        if node_key in self.db:
            self.logger.debug("Node %s already exists in db" % encode_hex(node_key))
            return

        if parent is not None:
            parent.dependencies += 1

        existing = self.requests.get(node_key)
        if existing is not None:
            self.logger.debug(
                "Already requesting %s, will just update parents list" % node_key)
            existing.parents.append(parent)
            return

        request = SyncRequest(node_key, parent, depth, leaf_callback, is_raw)
        # Requests get added to both self.queue and self.requests; the former is used to keep
        # track which requests should be sent next, and the latter is used to avoid scheduling a
        # request for a given node multiple times.
        self.logger.debug("Scheduling retrieval of %s" % encode_hex(request.node_key))
        self.requests[request.node_key] = request
        bisect.insort(self.queue, request)

    def get_children(self, request):
        """Return all children of the node retrieved by the given request.

        :rtype: A two-tuple with one list containing the children that reference other nodes and
        another containing the leaf children.
        """
        node = decode_node(request.data)
        node_type = get_node_type(node)
        references = []
        leaves = []
        if node_type == NODE_TYPE_LEAF:
            leaves.append(node[1])
        elif node_type == NODE_TYPE_EXTENSION:
            depth = request.depth + len(node[0])
            references.append((depth, node[1]))
        elif node_type == NODE_TYPE_BRANCH:
            depth = request.depth + 1
            for item in node[:16]:
                if is_blank_node(item):
                    continue

                # In a branch, the first 16 items are either a node whose RLP-encoded
                # representation is under 32 bytes or a reference to another node.
                if len(item) == 2:
                    if get_node_type(item) != NODE_TYPE_LEAF:
                        raise UnexpectedNodeType("Expected a node of type leaf, but got %s" % item)
                    leaves.append(item[1])
                elif len(item) == 17:
                    # NOTE: This can happen only if the RLP representation of all branch items fit
                    # in less than 32 bytes, which means the keys/values are extremely short, so
                    # it's probably not worth supporting it.
                    raise RuntimeError("If you get this, see the NOTE above")
                else:
                    references.append((depth, item))

            # The last item in a branch may contain a value.
            if not is_blank_node(node[16]):
                leaves.append(node[16])

        return references, leaves

    def process(self, results):
        """Process request results.

        :param results: A list of two-tuples containing the node's key and data.
        """
        for node_key, data in results:
            request = self.requests.get(node_key)
            if request is None:
                # This may happen if we resend a request for a node after waiting too long,
                # and then eventually get two responses with it.
                self.logger.info(
                    "No SyncRequest found for %s, maybe we got more than one response for it"
                    % encode_hex(node_key))
                return

            if request.data is not None:
                SyncRequestAlreadyProcessed("%s has been processed already" % request)

            request.data = data
            if request.is_raw:
                self.commit(request)
                continue

            references, leaves = self.get_children(request)

            for depth, ref in references:
                self.schedule(ref, request, depth, request.leaf_callback)

            if request.leaf_callback is not None:
                for leaf in leaves:
                    request.leaf_callback(leaf, request)

            if request.dependencies == 0:
                self.commit(request)

    def commit(self, request):
        self.db[keccak(request.data)] = request.data
        self.requests.pop(request.node_key)
        for ancestor in request.parents:
            ancestor.dependencies -= 1
            if ancestor.dependencies == 0:
                self.commit(ancestor)
