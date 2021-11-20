#!/usr/bin/env python3

import argparse, subprocess, shlex, re, webbrowser, sys, multiprocessing, os, signal
from pathlib import Path

parser = argparse.ArgumentParser(prog="ecco",
                                 description="Start ecco from Docker image.")
parser.add_argument("-t", "--tag", type=str, default="latest",
                    help="run specific version (e.g. '0.4', default: 'latest')")
parser.add_argument("-l", "--local", default="franckpommereau/",
                    action="store_const", const="", dest="repo",
                    help="run from local Docker repository")
parser.add_argument("-p", "--port", default=8000, type=int,
                    help="run jupyter on specific port (default: 8000)")
parser.add_argument("-n", "--no-browse",
                    dest="browse", default=True, action="store_false",
                    help="do not launch web brower")
parser.add_argument("-d", "--debug", default=False, action="store_true",
                    help="print Docker output and debugging messages")
parser.add_argument("-u", "--user", default="ecco", type=str,
                    help="run command as USER (default: 'ecco')")
parser.add_argument("-g", "--gui", default=False, action="store_true",
                    help="start Desktop integration GUI")
parser.add_argument("-c", "--chdir", default="/home/ecco", type=str, metavar="DIR",
                    help="set working directory to DIR (default: '/home/ecco')")
parser.add_argument("-m", "--mount", metavar="DIR", default=[],
                    type=str, action="append",
                    help="mount local directory DIR into the Docker container")
parser.add_argument("cmd", default=["jupyter-notebook", "--no-browser",
                                    "--port=8000", "--ip=0.0.0.0"],
                    type=str, nargs="*",
                    help="start a specific command (default: jupyter-notebook)")

args = parser.parse_args()

class Debug (object) :
    def __init__ (self) :
        self.debug = args.debug
        try :
            import colorama
            self.c = {"docker" : colorama.Fore.LIGHTBLACK_EX,
                      "info" : colorama.Fore.BLUE,
                      "warn" : colorama.Fore.RED,
                      "error" : colorama.Fore.RED + colorama.Style.BRIGHT,
                      "log" : colorama.Style.BRIGHT,
                      None : colorama.Style.RESET_ALL}
        except :
            self.c = {"docker" : "",
                      "info" : "",
                      "warn" : "",
                      "error" : "",
                      "log" : "",
                      None : ""}
    def __getitem__ (self, key) :
        return self.c.get(key, "")
    def __call__ (self, *args, kind="docker") :
        if self.debug :
            print(f"{self[kind]}{' '.join(str(a) for a in args)}{self[None]}")
    def log (self, *args, kind="log") :
        print(f"{self[kind]}{' '.join(str(a) for a in args)}{self[None]}")

debug = Debug()

argv = ["docker", "run",
        "-p", f"{args.port}:8000",
        "-u", args.user,
        "-w", args.chdir]

mount = set()
for mnt in args.mount :
    src = Path(mnt).resolve()
    home = Path("/home/ecco")
    dstparts = []
    for part in reversed(src.parts[1:]) :
        dstparts.insert(0, part)
        dstname = "-".join(dstparts)
        if dstname not in mount :
            dst = home / dstname
            mount.add(dstname)
            if str(src) == mnt :
                debug.log("mount:", src, "=>", dst)
            else :
                debug.log("mount:", mnt, "=>", src, "=>", dst)
            break
    else :
        debug.log(f"could not build a mountpoint for {mnt}", kind="error")
        sys.exit(1)
    argv.append("--mount")
    argv.append(f"type=bind,source={src},destination={dst}")

argv.append(f"{args.repo}ecco:{args.tag}")
argv.extend(args.cmd)

_url = re.compile(f"http://127.0.0.1:8000/\S*")
url = None

def gui (pid, url) :
    from PySide2.QtGui import QIcon, QPixmap
    from PySide2.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
    xpm = b"""/* XPM */
    static char *ecco[] = {
    /* width height ncolors chars_per_pixel */
    "72 72 214 2",
    /* colors */
    "   c #000000",
    " . c #AFAFAF",
    " X c #ADADAD",
    " o c #ABABAB",
    " O c #A9A9A9",
    " + c #A7A7A7",
    " @ c #A5A5A5",
    " # c #A3A3A3",
    " $ c #A1A1A1",
    " % c #9F9F9F",
    " & c #9B9B9B",
    " * c #999999",
    " = c #979797",
    " - c #939393",
    " ; c #919191",
    " : c #8F8F8F",
    " > c #8D8D8D",
    " , c #8B8B8B",
    " < c #898989",
    " 1 c #878787",
    " 2 c #858585",
    " 3 c #838383",
    " 4 c #818181",
    " 5 c #7D7D7D",
    " 6 c #7B7B7B",
    " 7 c #777777",
    " 8 c #757575",
    " 9 c #737373",
    " 0 c #717171",
    " q c #6F6F6F",
    " w c #6D6D6D",
    " e c #6B6B6B",
    " r c #676767",
    " t c #656565",
    " y c #636363",
    " u c #616161",
    " i c #5F5F5F",
    " p c #5B5B5B",
    " a c #575757",
    " s c #555555",
    " d c #535353",
    " f c #4F4F4F",
    " g c #FEFEFE",
    " h c #4B4B4B",
    " j c #FCFCFC",
    " k c #494949",
    " l c #FAFAFA",
    " z c #474747",
    " x c #454545",
    " c c #F6F6F6",
    " v c #F4F4F4",
    " b c #414141",
    " n c #F2F2F2",
    " m c #F0F0F0",
    " M c #3D3D3D",
    " N c #EEEEEE",
    " B c #3B3B3B",
    " V c #ECECEC",
    " C c #393939",
    " Z c #EAEAEA",
    " A c #373737",
    " S c #E8E8E8",
    " D c #353535",
    " F c #E6E6E6",
    " G c #333333",
    " H c #E4E4E4",
    " J c #313131",
    " K c #E2E2E2",
    " L c #E0E0E0",
    " P c #2D2D2D",
    " I c #DEDEDE",
    " U c #2B2B2B",
    " Y c #DCDCDC",
    " T c #292929",
    " R c #DADADA",
    " E c #D8D8D8",
    " W c #252525",
    " Q c #D6D6D6",
    " ! c #232323",
    " ~ c #D4D4D4",
    " ^ c #1F1F1F",
    " / c #1B1B1B",
    " ( c #CCCCCC",
    " ) c #191919",
    " _ c #CACACA",
    " ` c #171717",
    " ' c #C8C8C8",
    " ] c #C6C6C6",
    " [ c #131313",
    " { c #C4C4C4",
    " } c #111111",
    " | c #C2C2C2",
    ".  c #0F0F0F",
    ".. c #C0C0C0",
    ".X c #0D0D0D",
    ".o c #0B0B0B",
    ".O c #BCBCBC",
    ".+ c #090909",
    ".@ c #BABABA",
    ".# c #070707",
    ".$ c #B8B8B8",
    ".% c #050505",
    ".& c #B6B6B6",
    ".* c #030303",
    ".= c #B4B4B4",
    ".- c #010101",
    ".; c #B2B2B2",
    ".: c #B0B0B0",
    ".> c #AEAEAE",
    "., c #ACACAC",
    ".< c #AAAAAA",
    ".1 c #A8A8A8",
    ".2 c #A6A6A6",
    ".3 c #A4A4A4",
    ".4 c #A2A2A2",
    ".5 c #A0A0A0",
    ".6 c #9E9E9E",
    ".7 c #9C9C9C",
    ".8 c #989898",
    ".9 c #969696",
    ".0 c #949494",
    ".q c #929292",
    ".w c #909090",
    ".e c #8E8E8E",
    ".r c #8A8A8A",
    ".t c #888888",
    ".y c #868686",
    ".u c #848484",
    ".i c #828282",
    ".p c #808080",
    ".a c #7E7E7E",
    ".s c #7C7C7C",
    ".d c #787878",
    ".f c #767676",
    ".g c #727272",
    ".h c #707070",
    ".j c #6E6E6E",
    ".k c #6C6C6C",
    ".l c #666666",
    ".z c #646464",
    ".x c #606060",
    ".c c #5E5E5E",
    ".v c #5C5C5C",
    ".b c #565656",
    ".n c #545454",
    ".m c #505050",
    ".M c #4E4E4E",
    ".N c #FFFFFF",
    ".B c #4C4C4C",
    ".V c #FDFDFD",
    ".C c #4A4A4A",
    ".Z c #FBFBFB",
    ".A c #F9F9F9",
    ".S c #464646",
    ".D c #F7F7F7",
    ".F c #444444",
    ".G c #F5F5F5",
    ".H c #424242",
    ".J c #F3F3F3",
    ".K c #404040",
    ".L c #F1F1F1",
    ".P c #EFEFEF",
    ".I c #EDEDED",
    ".U c #3A3A3A",
    ".Y c #383838",
    ".T c #E9E9E9",
    ".R c #363636",
    ".E c #E7E7E7",
    ".W c #343434",
    ".Q c #323232",
    ".! c #E3E3E3",
    ".~ c #E1E1E1",
    ".^ c #2E2E2E",
    "./ c #DFDFDF",
    ".( c #2C2C2C",
    ".) c #DDDDDD",
    "._ c #2A2A2A",
    ".` c #282828",
    ".' c #D9D9D9",
    ".] c #262626",
    ".[ c #D7D7D7",
    ".{ c #242424",
    ".} c #D5D5D5",
    ".| c #222222",
    "X  c #D3D3D3",
    "X. c #202020",
    "XX c #D1D1D1",
    "Xo c #CFCFCF",
    "XO c #1C1C1C",
    "X+ c #CDCDCD",
    "X@ c #CBCBCB",
    "X# c #181818",
    "X$ c #C9C9C9",
    "X% c #161616",
    "X& c #141414",
    "X* c #C5C5C5",
    "X= c #C3C3C3",
    "X- c #101010",
    "X; c #C1C1C1",
    "X: c #0E0E0E",
    "X> c #BFBFBF",
    "X, c #0C0C0C",
    "X< c #BDBDBD",
    "X1 c #0A0A0A",
    "X2 c #BBBBBB",
    "X3 c #080808",
    "X4 c #B9B9B9",
    "X5 c #060606",
    "X6 c #B7B7B7",
    "X7 c #040404",
    "X8 c #B5B5B5",
    "X9 c #020202",
    "X0 c #B3B3B3",
    "Xq c None",
    /* pixels */
    "                                                                                                                                                ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N gX  +.0 4 3 =.>.E.N.N.N.N.N.N.N.N.N.N.N.N.N.N                             ) f r.d.u 6 q f !                          ",
    "  .N.N.N.N.N.N.N.N.N.NXX.vX&                .(.8 l.N.N.N.N.N.N.N.N.N.N.N                       / 3.~.N.N.N.N.N.N.N.N.NXo 0 `                    ",
    "  .N.N.N.N.N.N.N.N m.b.-                        .{.}.N.N.N.N.N.N.N.N.N.N                  X9.s.Z.N.N.N.N.N.N.N.N.N.N.N.N.N.Z.5X3                ",
    "  .N.N.N.N.N.N.N Y.`                              X- (.N.N.N.N.N.N.N.N.N                .#X2.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N M                ",
    "  .N.N.N.N.N.N.G._            .F.6 |X; *.W           W.G.N.N.N.N.N.N.N.N                 $.N.N.N.N.N.N.NX@ & 2 -.1.!.N.N.N.N.NX#                ",
    "  .N.N.N.N.N.N.l            .s.N.N.N.N.N.D.C           3.N.N.N.N.N.N.N.N               s.N.N.N.N.N.N H C             AX<.N.N Z                  ",
    "  .N.N.N.N.N KX7           q.N.N.N.N.N.N.N.A `        XO j.N.N.N.N.N.N.N            .-XX.N.N.N.N.N l U                  .h l.$                  ",
    "  .N.N.N.N.N 8          X7 F.N.N.N.N.N.N.N.N.k           ].N.N.N.N.N.N.N            .K.N.N.N.N.N.N.2                      .R._                  ",
    "  .N.N.N.N.N.(          .M.N.N.N.N.N.N.N.N.NX4           ;.N.N.N.N.N.N.N             3.N.N.N.N.N.N.l                                            ",
    "  .N.N.N.N N.-          .y.N.N.N.N.N.N.N.N.N E          .l.N.N.N.N.N.N.N            X;.N.N.N.N.N.N T                                            ",
    "  .N.N.N.N |            .1.N.N.N.N.N.N.N.N.N.L          .b.N.N.N.N.N.N.N            .T.N.N.N.N.N.NX3                                            ",
    "  .N.N.N.N.:            .].W.W.W.W.W.W.W.W.W G          .C.N.N.N.N.N.N.N             l.N.N.N.N.N g                                              ",
    "  .N.N.N.N %                                             e.N.N.N.N.N.N.N          X,.N.N.N.N.N.N v                                              ",
    "  .N.N.N.N $            .+X,X,X,X,X,X,X,X,X,X,X,X,X,.  A./.N.N.N.N.N.N.N           }.N.N.N.N.N.N.J                                              ",
    "  .N.N.N.N.=            X<.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N          X9 g.N.N.N.N.N l                                              ",
    "  .N.N.N.N '            .4.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N            .P.N.N.N.N.N.NX7                                            ",
    "  .N.N.N.N.L.*           4.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N             (.N.N.N.N.N.N P                                            ",
    "  .N.N.N.N.N.Y           G.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N            .w.N.N.N.N.N.N y                                            ",
    "  .N.N.N.N.N.i             E.N.N.N.N.N.N.N.N.N.N.N.N L.g.V.N.N.N.N.N.N.N            .m.N.N.N.N.N.N #                      .|X> T                ",
    "  .N.N.N.N.N V.X           a.N.N.N.N.N.N.N.N.N.N.N.3.    R.N.N.N.N.N.N.N            .% K.N.N.N.N.N.Z T                   d.I.N i                ",
    "  .N.N.N.N.N.N.a             q l.N.N.N.N.N.N.NX@.m      .@.N.N.N.N.N.N.N              .j.N.N.N.N.N.N K J          X7 hX4.N.N.N 7                ",
    "  .N.N.N.N.N.N.Z.S             !.i.&XoX+X0.a.R          .4.N.N.N.N.N.N.N              .*.O.N.N.N.N.N.N gX2 >.s.8X6.T.N.N.N.N.N ,                ",
    "  .N.N.N.N.N.N.N m M                                    .=.N.N.N.N.N.N.N                 [X .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N 1                ",
    "  .N.N.N.N.N.N.N.N j.s.%                             D ..N.N.N.N.N.N.N.N                  X1 $.N.N.N.N.N.N.N.N.N.N.N.N.N.N.J.rX,                ",
    "  .N.N.N.N.N.N.N.N.N.N F.s ^                   /.z _.N.N.N.N.N.N.N.N.N.N                       J.3 v.N.N.N.N.N.N.N.N.V ( eX:                    ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N H o :.a q 8.y O.[.N.N.N.N.N.N.N.N.N.N.N.N.N                          .*.Q t.d < ;.t w k.                           ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "  .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N                                                                        ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                               ) f r.d.u 6 q f !                        .N.N.N.N.N.N.N.N.N.N.N.N.N R.< = 2.a.w.4 {.A.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                         / 3.~.N.N.N.N.N.N.N.N.NXo 0 `                  .N.N.N.N.N.N.N.N.N.N Q uX#                X3 b.,.V.N.N.N.N.N.N.N.N.N.N  ",
    "                    X9.s.Z.N.N.N.N.N.N.N.N.N.N.N.N.N.Z.5X3              .N.N.N.N.N.N.N.N n p.-                          .` (.N.N.N.N.N.N.N.N.N  ",
    "                  .#X2.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N M              .N.N.N.N.N.N.N./ U                                X3 +.N.N.N.N.N.N.N.N  ",
    "                   $.N.N.N.N.N.N.NX@ & 2 -.1.!.N.N.N.N.NX#              .N.N.N.N.N.N.D.^             b &.OX*.1 t.o          .%X$.N.N.N.N.N.N.N  ",
    "                 s.N.N.N.N.N.N H C             AX<.N.N Z                .N.N.N.N.N.N w          X9.6.N.N.N.N.N.N E ^          X. c.N.N.N.N.N.N  ",
    "              .-XX.N.N.N.N.N l U                  .h l.$                .N.N.N.N.N SX5           r.N.N.N.N.N.N.N.NX>             *.N.N.N.N.N.N  ",
    "              .K.N.N.N.N.N.N.2                      .R._                .N.N.N.N.N.p            X+.N.N.N.N.N.N.N.N.N !           T.N.N.N.N.N.N  ",
    "               3.N.N.N.N.N.N.l                                          .N.N.N.N.N.W          .+.Z.N.N.N.N.N.N.N.N.N.v             I.N.N.N.N.N  ",
    "              X;.N.N.N.N.N.N T                                          .N.N.N.N c.%           B.N.N.N.N.N.N.N.N.N.N.q             @.N.N.N.N.N  ",
    "              .T.N.N.N.N.N.NX3                                          .N.N.N.NX$            .m.N.N.N.N.N.N.N.N.N.N.2             9.N.N.N.N.N  ",
    "               l.N.N.N.N.N g                                            .N.N.N.NX8             a.N.N.N.N.N.N.N.N.N.N.>            .x.N.N.N.N.N  ",
    "            X,.N.N.N.N.N.N v                                            .N.N.N.N @            .c.N.N.N.N.N.N.N.N.N.NX8             f.N.N.N.N.N  ",
    "             }.N.N.N.N.N.N.J                                            .N.N.N.N.7             p.N.N.N.N.N.N.N.N.N.N.;             x.N.N.N.N.N  ",
    "            X9 g.N.N.N.N.N l                                            .N.N.N.N o            .n.N.N.N.N.N.N.N.N.N.N.<             s.N.N.N.N.N  ",
    "              .P.N.N.N.N.N.NX7                                          .N.N.N.NX<            .B.N.N.N.N.N.N.N.N.N.N.4             r.N.N.N.N.N  ",
    "               (.N.N.N.N.N.N P                                          .N.N.N.N.'            .`.N.N.N.N.N.N.N.N.N.N 5             3.N.N.N.N.N  ",
    "              .w.N.N.N.N.N.N y                                          .N.N.N.N.NX%          .-.P.N.N.N.N.N.N.N.N.N z            ...N.N.N.N.N  ",
    "              .m.N.N.N.N.N.N #                      .|X> T              .N.N.N.N.N s            X8.N.N.N.N.N.N.N.N l }          .#.D.N.N.N.N.N  ",
    "              .% K.N.N.N.N.N.Z T                   d.I.N i              .N.N.N.N.NX2            .U.V.N.N.N.N.N.N.N.e             t.N.N.N.N.N.N  ",
    "                .j.N.N.N.N.N.N K J          X7 hX4.N.N.N 7              .N.N.N.N.N.N.R            .b.P.N.N.N.N g.7X7          X7.).N.N.N.N.N.N  ",
    "                .*.O.N.N.N.N.N.N gX2 >.s.8X6.T.N.N.N.N.N ,              .N.N.N.N.N.N.}.X            .o.b.d.i.l.{              .e.N.N.N.N.N.N.N  ",
    "                   [X .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N 1              .N.N.N.N.N.N.N.&.+                                   e.N.N.N.N.N.N.N.N  ",
    "                    X1 $.N.N.N.N.N.N.N.N.N.N.N.N.N.N.J.rX,              .N.N.N.N.N.N.N.N ~.(                            X, $.N.N.N.N.N.N.N.N.N  ",
    "                         J.3 v.N.N.N.N.N.N.N.N.V ( eX:                  .N.N.N.N.N.N.N.N.N j X.HX7                  .] ,.I.N.N.N.N.N.N.N.N.N.N  ",
    "                            .*.Q t.d < ;.t w k.                         .N.N.N.N.N.N.N.N.N.N.N.N cX=.9 2.f 0.p.w.;.T.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                        .N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N.N  ",
    "                                                                                                                                                "
    };"""
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    def browse () :
        webbrowser.open(url)
    menu = QMenu()
    action = QAction("Open in browser")
    action.triggered.connect(browse)
    def stop () :
        os.kill(pid, signal.SIGINT)
        app.quit()
    menu.addAction(action)
    quit = QAction("Quit")
    quit.triggered.connect(stop)
    menu.addAction(quit)
    pix = QPixmap()
    pix.loadFromData(xpm)
    icon = QIcon(pix)
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)
    tray.setToolTip("ecco")
    tray.setContextMenu(menu)
    app.exec_()

try :
    debug.log("starting Docker")
    debug("running:", " ".join(argv), kind="info")
    sub = subprocess.Popen(argv,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding="utf-8",
                           errors="replace")
    for line in sub.stdout :
        debug(line.strip())
        if url is None :
            match = _url.search(line)
            if match :
                url = match.group()
                debug.log("jupyter-notebook is at:", url)
                if args.gui :
                    proc = multiprocessing.Process(target=gui,
                                                   args=(os.getpid(), url),
                                                   daemon=False)
                    proc.start()
                if args.browse :
                    debug("starting browser...", kind="info")
                    webbrowser.open(url)
                    args.browse = False
except KeyboardInterrupt :
    debug.log("terminating...")
    sub.terminate()
