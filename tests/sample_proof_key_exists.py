# flake8: NOQA: E501
# This proves that the given key (which is an account) exists on the trie rooted at this state
# root. It was obtained by querying geth via the LES protocol
state_root = b"Gu\xd8\x85\xf5/\x83:e\xf5\x9e0\x0b\xce\x86J\xcc\xe4.0\xc8#\xdaW\xb3\xbd\xd0).\x91\x17\xe8"
key = b"\x9b\xbf\xc3\x08Z\xd0\xd47\x84\xe6\xe4S4ndG|\xac\xa3\x0f^7\xd5nv\x14\x9e\x98\x84\xe7\xc2\x97"
proof = (
    [
        b"\x01\xb2\xcf/\xa7&\xef{\xec9c%\xed\xeb\x9b)\xe9n\xb5\xd5\x0e\x8c\xa9A\xc1:-{<2$)",
        b"\xa2\xbab\xe5J\x88\xa1\x8b\x90y\xa5yW\xd7G\x13\x16\xec\xb3\xb6\x87S9okV\xa3\rlC\xbfU",
        b"\xd6\x06\x92\x9e\x0b\xd310|\xbeV\x9d\xb4r\xdf0\xa5Q\xfb\xec\xb9I\x8c\x96r\x81\xeb\xefX7_l",
        b"\xa8\x88\xed@\x04\x7f\xa6\xbe&\x89&\x89T\t+\xac\xb8w\x8a\xebn\x16\x0c\xe1n\xb4?\xad\x14\xfdF\xff",
        b"\xc9\t\xd0\xaa\xb0:P\xdc\xea\xedX%\x04\x9a\xbe\x1f\x16\x0cf\xbc\x04P#@\xfd\xd60\xad\xecK\x8b\x08",
        b"x\xff\xb2\x9ajO\xbc\x1bjR\x80$I\xe6\x95\xf6Tow\x82\xf9\x01\xa8V\xa9\xaa4\xa6`\x88\xf9\x10",
        b"I\x1cQc\x8a\xeda\xf8\xd1D\x01GT)\xc9\x02O\xef\x8d\xcc\\\xf9\xe6}\x8a~\xcc\x98~\xd5\xd6\xb6",
        b"U'\xa2\xa0 \xe4\xb1\xb6\xc3\xcd4C_\x9c]\xb3P\xa8w\xef\x8c\xde\xc2\x02^v\xcd\x12\xed%\x89\xa5",
        b"(\xa6x\xfa\xbe\xc3\x9a\xae\xaa\xe9\xbcv#u\\\xdfo\x14\x9a3\xbc\x89c\xc1\xfe\xdf[{|\x02P\x03",
        b"\xcf5\x07\x8f3\xa9\x1f\x19Q\xbb\x11\x8a\xb0\x97\xbe\x93\xb2\xd5~\xe2\xe06\x07\xc37\x08vg\x80 BD",
        b"U\x8e/\x95&\n\xc5\xf1\xd4\xc3\xb9\xa84Rd\xaa\x80\xfe8\xf1\xcf G\xcc\xe3\x99\x01\x07\xceH\x9a`",
        b"W\x1f\xb5\x1c\xec\xf7\x0b\x86\x15\r\xf9\xf9\x94\xcd|\xe6B\x9f\xa8l\x8d]D\xf7\xba\xee:\xc0\\\x11\xb8\x08",
        b"\xf5i\xee)\xc4\xd24\xfc\x8f\xba\xc0vS\x1dU>\xccz\xd18\n\xa2+\n\xcf\xe2i*\xee\x18\xe8\xc1",
        b"\x9dmSX\x1e\xee\xf7`\x1d\x0cO\xfcF\xe4\xbd\x0cE2\x10H6\xf0\x93|\xd5z\xe7=\xebbJ\xd6",
        b"u\x08\x92\x08\xa5Nl\x938\x03\xa3\xe2O\xe8\xfe\xb1\xc4\x87\x8c\xb8q\x9eb\x89b\x96\x98\xd7\xf22\xb9\xa2",
        b"\xa6V\xb5?\xcc\xd2\xc8*ME\xe7\xcf\xf8\xad\xf8\xdb\xe7\xf8\xf6D\xd5<\x1c\x95F\x13\x0e\x06rz\xe5m",
        b"",
    ],
    [
        b"\xb3\x03\xa9\xc11\x87mQ\xa1I2D4jg\xfe\xd0%k\xf2\r]\xb0\x0e\xeb'\x17\xedx\xc9Uj",
        b"L/\r$7-\xa5\xdf x\x9c\xbc\xc4\x99\x1e\xc5\xd8\xb5\xaf\xd1\xd1\xae\xe6L\xeco\xc4\xe2RUe\r",
        b"\xbeSp\xf5\xef\x02\xcd\x83\xb2\x0b\xa06\xfd\xca\xbb\xed_\xf2}\xf7\xea\xb3\x84\x17\xed\xcc\x19mF\x13(\xf3",
        b"\xfb$IYR\x9f\x04p\x01\x1d}\x88\x0b\xed'\x8e%\x9b\xc9\xeaN_\xab\xf9\xc9\x9d\xac\xa9\xb3\t\x1eq",
        b"\xaab\xeb\x14\xc2\xf6}%\xaa+0\xb5\xc1\x0f< \xc5ma\xb1c\xeb\xdd\xca\xc0\x90\xe2L\x8b\xe9\xfe/",
        b"\x91l\x9d\xa2\x84\xbf\xc1\x05\xe2S\x0e\xc9`\xc0^}Q!\xc4ml-\xec\xf4R$\xf6\x8a\xd3\xc6\xf1j",
        b"\xf3\x13\xde\xe0L\xdb\x96E`Q\xdf\xa1\x13\x01b5\xe4k\xde\xde\xbf\xb10\xaf\xe61Z\xdbZ\xd47\xf4",
        b"\t\x81\xb0\xea*\xec\xd0\xc3\x16\xee\xed~\xdc\x98e\x90\xf2~p\xbbSY\x19\xcfl\xc4)\x01\xc2\xd9\xc91",
        b"-\xda%\x8a\xc5jA-\xe5 lIp\xbe\xb3h\x98\x0f\x80q\xed\xab\x89KN\xdd\xa6\xcb;\x98\xb08",
        b"\x13\x97\x12f\xa31\xfa}\xf1\xfe\x19\xfa\x0b\xe6\x89\x9a\xcb\xf5\xed\xf3Q\x98O=\xa3\xb0e/\xd9\x9fy\x08",
        b"f\xba%\xfb\xbfE\x1d]\xb3\x05\xe4$\xa5\xd2G\xecc\xe5#\x0f,\x91\x8bN9a\x8a\xd1L\x16l\xa5",
        b"#p\x15\x8bU\x04\x88/K|4a\xfc\x0e.Zm^{\x15uk\x8d\xe4_\xfe\xee\xae\xb99\xd1\x8e",
        b"C \x9f\xb3y\xf3d.\x8b\t\x1cF\x9eL\x08\x07y\x08\xb9\xe1\xffM\x87\xfd\xd6\xfd\xdb\x8f\x94\x9e\x88\xc2",
        b"\x17X\x1f/\x8b\x82\xf5\xe4\x02\x84}\xbe\x9bz` \x94'\"_\x9c\xff\x06\t>\x8a\xd7oK\xf9\xf5w",
        b"6Q\x8db\xd8\\\x84_Rin\x18\x1f\x17\x89\x7f@\xd6\xbb%>\xafa'\x80A\xa7\xd8}d\x07\"",
        b"\xccgm\xf7\x05\xc8\xe4G\xf4\xb3\x18\xc7\\.\x0b\xa25]\xdc\x80w\xda\xc9;\xde\x9b\x03\xa0LS\xce\x8c",
        b"",
    ],
    [
        b'\xe4\xd3\x15\xe0\xaa\x0f\xf9\xd0\xa6\xc2\xc8B_\xaf"0\x8c\xea;\x91\xe4E\x04\xec\x901yZ\xd6>\xadc',
        b"wM\xce\x16JS:\xe96\x98\x12|\xa0\xc9~G\xbb\xc7u8\xc8\x93\x9b\x05\x92yh\xaa\xda\x94NK",
        b"\x89\xc7\xa2\xbd\xe1\xda\x06$|\xde\x03\xd9RS\x90\x84\xe7\x05\x0cc\xdfy\xb0\xfb@\x065\xdb8\xa9\xef\x1f",
        b"@\x11>\xe8\xb8\x19\xb7\xc7@\x92m$\x93 \x08\xc5\x15\xbd\x97\xb0;\xf5\x05q;\xb5\xc69\xd3E\xc4\x0e",
        b"\xd5_ol\x05o\x8e\xf0V\xd2\xa0n\xe7CxR\xc9\x92HTQhkc\x10K\xad\xfdU\xe9\x97\x8f",
        b"v\x7f\xc5KB\xdaYS\xa1\xbf \xda\xe2\x99\x84\xef,\x92\xdd\xc9\xb8\x9eo\xfcv(\x95\xff\x94t\xbc5",
        b"\xcbQ\x962!$\x1f\xdc\xdb\xfe\xef'\xc8\xc8O\xec\xa2\xae\xd3P\x88\xbf\xbd!\xea\x0e\xb0\x89\xe9\xdd\xf3w",
        b"H\xb8\x1b\xc3&\x86|!o\x003/\xc7K\xc9+,K\xe1y\xf2\x86\xa9*H\x05W\xcd\xf8\x8b\xb5\n",
        b"\x06\xc5\xa1\x83\xe4\xb4\xdc\xbf\xc0\x8c4Q\x93\x14W\xaf\xbb\xe9f\x82\xa2\x8d\xa3m\xda\xed\xc0W\x88UA\xd9",
        b"\x9czV\x7f$\xa8\xb9\xf3\xc1W0\x19\xac\xc5\xaap\x03?*\xe6\xd6\xee<\x0b\xafr\xf6ji\xd9\x87\xed",
        b"\xc7\x1d\xca\x95\xab~\xd3|\xa6\x9f\xba\x9e\xd5KxI\x95Y\xadx\xb8\xda\xa7!\xba\x93\xbbB,\x97n\xe4",
        b'\xd7"\x13\xca=\xa9|e\x11\x8f%\xb2^\x1b\xa6\xff\x93Z\x8b(\xca\xab\x12\xed\x8b3\x0f\xe0\xa7U\xa9\xe1',
        b"\xc2\xb4\x98\xb7\x08\x18#i7\x81\x85\xfd\xc3\xc6k\x12\x86\x99\xa55\x0c8\xd3\xbc\x9d\xc8\xe0\xd3\xcd=\xc6x",
        b"\xad\xf0\xea&\xf4\x8f=5\xe1\xb5b\xc1}\xba\xa1\n \xa4\xb7J2\x1f\xd7\xc9\x1d\xa4\xc2\xaf\xb7O\xb2\x12",
        b"\xd5~\x94\x99~Vy,4\xedMJ\x1a\xda3\xe7\x90\x91\xd4\xafw\xba\xbf\x89`\x0e\x99s\x93E\xdf%",
        b"\x82\xd2O\x16\xca{\x15\x87\xef-\x8a\xea\xb9\xcd\xfc\x82\x84\x99\xdco\xc1\x1eg\xf3-\x07\xf8\xa3\xed\xffx\x85",
        b"",
    ],
    [
        b"\xc5\xa5\xd38zu\xfc\xe9\xe2j\x97\xf0\x81T$\xee5\x94AC\xb1\x85\x0c\xef\x10\xcb`Z\xfcT'\xcb",
        b"ZU\xe4?lj\x05\xf8\xbc\xa7\xf1\xe4\xdb\x08M\x06\xad\xbf\xb3s\xfa\xcaS\xb9{U\xd2n\x981+|",
        b'l\x0cL\xfb\\(g\xb47\xc2<\xcb\x14\xf3\xa9l\x01#\xdb"|\xdc\xfd\xa0#\xa2\x89\xcfx\x97\xb4\x8e',
        b"\x0b\xe7$\x1d\xa2\x1c\\\xa5)t\xd6\x82\xec\xed\x02]\xdd\xefz\xa3C`\x1b\xda\x81\t\xb3\x14\xdf5\xbb\xcb",
        b"\xe7%b2\xd4\xc6\x98\x90\xd8:B\xa4\x9e\n\xc6\xa1\x01\xac\x94\xbdr\xca\xdd\x8a\xa8\xe8\xc6F\xed\x04\xe9\x14",
        b"\xa7\xac\xc0S\xcbo\x98\xebJ)\xb1\x8b{\xda,\x98\xf2M\xca,\xcd\xc4%\x94\xe4\xdc<\xf5o}\x90\x1d",
        b"[\xd9}F\xe2\n\x84\xbc\xa0\x81\x0f\xb9\x0b]\x0c\x10%\x9d\r\x00RZgbV*2b\xd1z\xb5\xd3",
        b"\xac\xcag\xdb\xc3y\x91\x82\xddu\xad\x85%g\x82\xa0\r\xf4\x99^=\x14h\xee\xac\x81/o\xe6\xe4\xec\x0c",
        b"8\xeb\xed\x80}2\xd9.\x0e\xeb\x92\xa7\xae\xeb\x8d\x9b>8<\x9d\xc4\x05\xf2W;F\xce!\t\x15\xb2\xe3",
        b"*\xed\xbfJ\x80\x9f7\xd1\xcd\xeft\x89.e\x02M\r\x85D-\x9bL\x8d\xac*3h\xf3\x9f\xde\xe0F",
        b"d\xf9\xdf\xfb\xfa`\x97:\x11\xc4\x89u_\xe9&\xd0LX;r\x12\x86\\,}\x7f:\xbc\xf9\x9a\xd2\xe9",
        b"\x94\x80\xd4\xb8\xe4\xa6\xd4\x9cS\xcc\xc7*xo]2y~\xd6\x18a\xfb\xafP\x19\x87\xe7:\xb1r\x96\xdc",
        b"\x1c\xdar\xc1\x18\x1f\x0b\xf3\xe2\xf0\xf1<\x05\x88\xa4\x01J,\xc2\xa1\xbd`L\x8b\x95\xa6\xbdze4&\xc1",
        b">0\x01SdF=\x8c\xa7\x1d4\x1elOt\xcd;,|\xf0l\xe9O\x83\xf3\xc0rm\xb6\x82\xaa\x08",
        b"\xd0\xef\x12\xc5<\\\x00\x82$\x98\x8d\xb6\xa7l\xd6w\xa3\x00<D\x15\xf7\xd6\xc9\xd0\xfb\xd3\x9f\xed,\x9e\xf7",
        b"\xa6->\xb1\x80jz\xc3\x8a,5\xb8\xf8\xbf\xb4^\x880\x824A\xfa\xbf\x0e\x1f\x9b /\x02\xadhx",
        b"",
    ],
    [
        b"\xc1\x17\xa1{\x135'>\xce\x8a\xe8;\x84V\x8c\xfer\xdaZS\xc7v\xd7\x18\xfb\xe3\xbf\xff\x92\x87@D",
        b'\x06\xb9c\xad\x8d2\xc0WU\xaf"w\xe5>\x1a\xfd\x02\xf1\xdd\x91$h/\x02)\xc6\xd3\xbc\x17\xc42\xe8',
        b"\xc4\xa2\xb3*k\xa8\xc8\x124\x86\xa0\x9b\xad\xfa\xb9$5?\xc6\x0c]\x98Kb\xd13\xdb:\x85\xed\xe1[",
        b"%\xa4>aM\x08\xbet\x1b\xc8\xb5\xf2c.9o!\x03G\x99_\n\xef\x93OA^\xabC\x91\xce\x97",
        b"\xc9T\xc1\xf6\xc8\xbe\xd8h\x86\xfey\x82Evg\xe1zP\x9ct\x98(\x01\xf5\xfc\xf8\xbe\xf6\x1d\xc0\x15\x8e",
        b'\xd3\xf1\xe6T\xd7"\xba\xdeipC\xe5\xe1\x04\x0e?o\x84\xcb\x1aE\x18\xd0\xa36\x0eC\xc7D>\x12 ',
        b"\xe0\x06\x0c\xaf\xec\xe3op*j\xcd\x84\xef\x9b\x82a{,\x1c\x98\xba-\x10\xf9\x7f+\xb6\x8a/q,\xeb",
        b"\x8a'\xeb\x1a\xe8i\x91S\xf3;\xa8[f-\xb02\x01?\xac\xe4Ds\xd8E\xa0\x87\x8a\xec]\x9b?\x9e",
        b"\xcf\x0cM\xbd\x92\xbbaS\x9d\xd0:\x7f\xfe\xd5\x08\xac\xe4\xb5\x81ga\xc2>\\\x89\x95\x08\xd6C\xf9\xe6\xb7",
        b"\x9bh\xd3\xb0x\xf0\xfa5\xa6vV\x96_\x16\x9dx\x95B2\xa9\xcem\xc8\xb9\xaf\xb9\xff\n\xae\xc7\x14\x13",
        b"H\x03\x82\xd6\xbd\x00Z\r\xa03YQ\xa4\xfa\xcdl\xea8g{L\x16\x18\xca\xdb\xb75~\xff\x1b]&",
        b"A?l1\xbf\x04\xc3Qs\x9b\x08c\xc3|\xf5D6\xa2\x82\xf8\xd3\xf4@\xab\xa0oDx\xc4\xffY*",
        b"\x0c\xd7U\x880\xa0\xd3\xad\xdd\xda\xdb\x01\xac\x99ya:\xeb\xab8K%\xaf\xc4\xf1G\xd3*\xb7\xae\x01*",
        b"\xb8s\xab\x0e\xf4\x90\xdb\xce\x0b)l\xb3\x7f\xf1p\xc6&\x0eh\xfb\xc8\xd7\x88`\xcd\xdc\x97-l\xb6L\x82",
        b"x\xf2\x15\x85\xe9\x01\xd8\xdc\xc5\xbc\xb7\xda\xcd$\xf0\xae\xc9\x01\xcdHZ\xb8)\x97\x11\xff\xcc7\xa5\x98\xb4\xb6",
        b"\xf3\xb6\xdd\xe9\xb1\x93\x08A\xda\xa39\xfe$\x8dO\n$ Mn\"-'\xa5$F5\xae\xcd>\xa2\x0c",
        b"",
    ],
    [
        b"\x82\x8b\x9d\x85\x0b/\x83\xacmb\x07\x89h\xa5\x86R\x8e\xf4\xd9_\x00\t\xeb\xb3>\\@\x11\xecOp\x7f",
        b"",
        b"",
        b'"\xee\xd9\x89<\xc3_\xca\xe9\xed\xc2v\r,\x9e\x10\x1c\x07\xe8E\xbd\x10\x9a\x16_:hk\xb9Om\xf2',
        b"",
        b"",
        b"\x11]i\xb3t6\xabKF\xc0\xa9\x81z&\xdf\x02\xcaRQ\x82\x92\xac\xf1\xf9~\x94\x94tM9\xbe\x1a",
        b"\xd0dY\xbc\xbe\xe5\xa8\x93\xc8e\xbd\x15\xf8\xb6b\x9a+\xbeh\xeb\x9d\x85\x1f(\xee\xd5\xb2 \xf2\xea\xa1\xf2",
        b"",
        b"`\xa8\xcd0:I\xdd\xd7\xa1\xc9W\r\x00\xa6\x1b\x0cM\xbb8\xb0Z\x8b\xe2\x87\x16\x0f\x99U\xf7\xdf\xc4U",
        b"",
        b"\xbcR\x17x\x12Y\xf1r\xb9c\xf5\x17#\xcd\xdb\xd5\x1c0\xd2\xda~\x99a\x96\xd5k\xef\x94\x0f\xd0$\xcb",
        b"!\x16\xaee\xb5H7X\xd5\tA\xb5{\x98\x8f\x12\x0bX\x85K\x184\x04\xcf\x80\x17\xf81V\xbc\xed\x9c",
        b"\x00\x08C^\xb5\xcfb\xb3\x13\xf0\x95S\x8eyQ\xe8\xdf\x9bI\xfe\xa2\x9c\x91@_\x16\x9d\x82w,u\x86",
        b"6&\x99Z\xae\xe6r\xab\xec\xb3X\x87\\\x02\x99>\xfa\xebP:\xd5\xd2t\xe2p\xc7\xe2\xe0\x0e\x95\xf9D",
        b"\xcf\x7f\x99\x9a\x1c\x18\xa6\x9av\xe6\xa2\xd5\xb3E\x8aJ\x18\xa7\x8c\xc0\x07\xda\xe9\x0bi\r\t\x0f\x9b\x06\xf8S",
        b"",
    ],
    [
        b'\x07\x83C\xd1X\xdf\xddJ\xd4\xf2\x7f3+\n\x95\xb2\x89\xd2"\x9d\xc5S\xfb\xfc\x9ed\x8d\xd2\xd2\xe5\x99B',
        b"",
        b"",
        b"",
        b"",
        b"-m2\x00\xef\x95\xcd\xfe\xf8\x9e\x0b\xbf\xae\xd8\xb4\xd2\xa1*\xfde\xaa\xb1\x8a\xdd\x1d\x07\x03\xc7,<\xe8\xe7",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
        b"",
    ],
    [
        b"8Z\xd0\xd47\x84\xe6\xe4S4ndG|\xac\xa3\x0f^7\xd5nv\x14\x9e\x98\x84\xe7\xc2\x97",
        b"\xf8D\x01\x80\xa0U\xbd\x1daQ\x97{bg,!\xc2uK\xbe\xeb;\x82x\xb2\xe0\xc3\x8e\xdc\xd9I\x84n\xe3b\x8b\xf1\xa0\x1e\x0b*\xd9p\xb3e\xa2\x17\xc4\x0b\xcf5\x82\xcb\xb4\xfc\xc1d-z]\xd7\xa8*\xe1\xe2x\xe0\x10\x12>",
    ],
)
