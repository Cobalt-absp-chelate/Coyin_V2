from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, QRect, QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QImageReader, QPainter, QPainterPath
from PySide6.QtQml import qmlRegisterType
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtSvg import QSvgRenderer


BANNER_LAYER_ORDER = ("background", "midground", "foreground", "overlay")


@dataclass(frozen=True, slots=True)
class BannerPreset:
    preset_id: str
    title: str
    description: str


BANNER_PRESETS: tuple[BannerPreset, ...] = (
    BannerPreset("preset_academic", "浅蓝学术科技风", "浅蓝渐变、论文线条、节点与几何光斑"),
    BannerPreset("preset_graph", "夜间赛博城市", "动漫风夜间都市、霓虹高楼与近景栏杆层次"),
    BannerPreset("preset_warm", "黄昏校园", "治愈系黄昏天空、校园轮廓、树影与窗框前景"),
    BannerPreset("preset_glass", "极简玻璃空间风", "灰蓝渐变、玻璃块与高光线条"),
)

_PRESET_TITLES = {preset.preset_id: preset.title for preset in BANNER_PRESETS}


def default_banner_preset_id() -> str:
    return BANNER_PRESETS[0].preset_id


def banner_preset_entries() -> list[dict[str, str]]:
    return [
        {
            "preset_id": preset.preset_id,
            "title": preset.title,
            "description": preset.description,
        }
        for preset in BANNER_PRESETS
    ]


def banner_preset_ids() -> set[str]:
    return {preset.preset_id for preset in BANNER_PRESETS}


def preset_layer_path(assets_root: Path, preset_id: str, layer_name: str) -> Path:
    return assets_root / preset_id / f"{layer_name}.svg"


def ensure_default_banner_assets(assets_root: Path) -> Path:
    assets_root.mkdir(parents=True, exist_ok=True)
    builders = {
        "preset_academic": _preset_academic_layers(),
        "preset_graph": _preset_graph_layers(),
        "preset_warm": _preset_warm_layers(),
        "preset_glass": _preset_glass_layers(),
    }
    for preset_id, layers in builders.items():
        preset_dir = assets_root / preset_id
        preset_dir.mkdir(parents=True, exist_ok=True)
        for layer_name, payload in layers.items():
            path = preset_dir / f"{layer_name}.svg"
            path.write_text(payload, encoding="utf-8")
    return assets_root


def _svg_document(content: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="240" viewBox="0 0 1600 240">'
        f"{content}</svg>"
    )


def _preset_academic_layers() -> dict[str, str]:
    return {
        "background": _svg_document(
            """
            <defs>
              <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#eef7ff"/>
                <stop offset="44%" stop-color="#cfe6fb"/>
                <stop offset="100%" stop-color="#99c6e7"/>
              </linearGradient>
              <radialGradient id="halo" cx="78%" cy="14%" r="58%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.94"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect width="1600" height="240" fill="url(#bg)"/>
            <rect width="1600" height="240" fill="url(#halo)"/>
            <path d="M0 168C182 148 314 138 466 146C650 156 760 206 972 204C1188 202 1342 154 1600 112V240H0Z" fill="#d6e9f8" fill-opacity="0.96"/>
            <path d="M0 202C174 182 336 174 538 178C736 182 878 218 1110 216C1292 214 1434 192 1600 170V240H0Z" fill="#c1dcf2" fill-opacity="0.92"/>
            """
        ),
        "midground": _svg_document(
            """
            <defs>
              <linearGradient id="line" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#89b6d8" stop-opacity="0.42"/>
                <stop offset="100%" stop-color="#487aa4" stop-opacity="0.62"/>
              </linearGradient>
            </defs>
            <g fill="none" stroke="url(#line)" stroke-width="1.9">
              <path d="M32 176H1568"/>
              <path d="M60 138H1480"/>
              <path d="M128 42V206"/>
              <path d="M324 24V194"/>
              <path d="M528 18V210"/>
              <path d="M742 22V214"/>
              <path d="M968 24V198"/>
              <path d="M1188 28V206"/>
              <path d="M1418 34V214"/>
              <path d="M136 182C238 108 374 72 540 82C702 92 792 132 908 128C1048 122 1138 64 1288 64C1386 64 1462 86 1520 116"/>
              <path d="M94 126C244 72 372 60 530 70C700 82 814 138 1002 136C1172 132 1304 88 1508 44"/>
              <path d="M204 160C284 120 354 112 430 124C512 136 586 170 670 164C760 158 828 118 904 108C998 96 1082 120 1178 152"/>
            </g>
            <g fill="#4d83ab" fill-opacity="0.60">
              <circle cx="176" cy="122" r="7"/>
              <circle cx="302" cy="84" r="5"/>
              <circle cx="490" cy="98" r="8"/>
              <circle cx="692" cy="112" r="6"/>
              <circle cx="838" cy="128" r="7"/>
              <circle cx="1024" cy="112" r="6"/>
              <circle cx="1204" cy="78" r="8"/>
              <circle cx="1392" cy="100" r="7"/>
            </g>
            """
        ),
        "foreground": _svg_document(
            """
            <defs>
              <radialGradient id="softA" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.88"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
              </radialGradient>
              <radialGradient id="softB" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#9dc7e8" stop-opacity="0.86"/>
                <stop offset="100%" stop-color="#b8d2ea" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="1328" cy="92" r="78" fill="url(#softA)"/>
            <circle cx="1208" cy="74" r="58" fill="url(#softB)"/>
            <circle cx="258" cy="72" r="48" fill="url(#softA)"/>
            <path d="M1074 70L1168 50L1234 102L1138 128Z" fill="#d9ecfa" fill-opacity="0.78"/>
            <path d="M124 62L228 42L280 84L178 112Z" fill="#d5eaf9" fill-opacity="0.64"/>
            <rect x="736" y="52" width="132" height="20" rx="10" fill="#c8def0" fill-opacity="0.80"/>
            <rect x="896" y="88" width="94" height="16" rx="8" fill="#e7f2fb" fill-opacity="0.76"/>
            """
        ),
        "overlay": _svg_document(
            """
            <defs>
              <linearGradient id="wash" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.36"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            <rect width="1600" height="78" fill="url(#wash)"/>
            <g fill="none" stroke="#ffffff" stroke-opacity="0.72" stroke-width="1.8">
              <path d="M1110 46C1188 20 1292 18 1408 44"/>
              <path d="M1090 138C1186 110 1306 106 1446 132"/>
            </g>
            <g fill="#ffffff" fill-opacity="0.56">
              <circle cx="1254" cy="54" r="6"/>
              <circle cx="1358" cy="68" r="4"/>
              <circle cx="1452" cy="90" r="5"/>
              <circle cx="214" cy="52" r="5"/>
              <circle cx="282" cy="74" r="4"/>
            </g>
            """
        ),
    }


def _preset_graph_layers() -> dict[str, str]:
    return {
        "background": _svg_document(
            """
            <defs>
              <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#0a1220"/>
                <stop offset="44%" stop-color="#101c34"/>
                <stop offset="76%" stop-color="#17355d"/>
                <stop offset="100%" stop-color="#1c4c7c"/>
              </linearGradient>
              <radialGradient id="moonGlow" cx="78%" cy="18%" r="26%">
                <stop offset="0%" stop-color="#dff2ff" stop-opacity="0.70"/>
                <stop offset="100%" stop-color="#dff2ff" stop-opacity="0"/>
              </radialGradient>
              <radialGradient id="haze" cx="64%" cy="70%" r="58%">
                <stop offset="0%" stop-color="#3d78aa" stop-opacity="0.26"/>
                <stop offset="100%" stop-color="#3d78aa" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect width="1600" height="240" fill="url(#bg)"/>
            <circle cx="1244" cy="56" r="26" fill="#dff1ff" fill-opacity="0.76"/>
            <rect width="1600" height="240" fill="url(#moonGlow)"/>
            <rect width="1600" height="240" fill="url(#haze)"/>
            <path d="M0 152C122 138 258 136 402 142C588 150 718 182 888 182C1098 182 1268 144 1600 100V240H0Z" fill="#0d1730" fill-opacity="0.70"/>
            <path d="M0 196C146 166 314 144 486 152C706 164 844 228 1084 224C1258 220 1432 188 1600 148V240H0Z" fill="#142f4d" fill-opacity="0.94"/>
            <path d="M0 212C180 194 338 186 512 190C720 194 874 224 1106 222C1302 220 1452 198 1600 178V240H0Z" fill="#1d476b" fill-opacity="0.78"/>
            <g fill="#aacff3" fill-opacity="0.28">
              <circle cx="184" cy="52" r="2"/>
              <circle cx="252" cy="74" r="1.8"/>
              <circle cx="336" cy="58" r="2.2"/>
              <circle cx="418" cy="78" r="1.6"/>
              <circle cx="1468" cy="48" r="1.8"/>
              <circle cx="1524" cy="72" r="2.1"/>
            </g>
            """
        ),
        "midground": _svg_document(
            """
            <g fill="#102542">
              <path d="M0 186L0 134L64 134L64 116L104 116L104 152L148 152L148 88L198 88L198 124L248 124L248 98L296 98L296 142L346 142L346 110L392 110L392 160L438 160L438 82L486 82L486 152L532 152L532 104L584 104L584 140L636 140L636 74L690 74L690 152L742 152L742 120L786 120L786 150L840 150L840 94L904 94L904 156L962 156L962 108L1020 108L1020 144L1088 144L1088 86L1144 86L1144 150L1212 150L1212 98L1274 98L1274 138L1334 138L1334 78L1408 78L1408 146L1482 146L1482 104L1546 104L1546 136L1600 136L1600 186Z"/>
            </g>
            <g fill="#8fc9ff" fill-opacity="0.58">
              <rect x="84" y="128" width="8" height="12"/><rect x="96" y="128" width="8" height="12"/><rect x="84" y="144" width="20" height="10"/>
              <rect x="176" y="102" width="8" height="12"/><rect x="188" y="102" width="8" height="12"/><rect x="176" y="118" width="20" height="10"/>
              <rect x="456" y="96" width="8" height="12"/><rect x="468" y="96" width="8" height="12"/><rect x="456" y="112" width="20" height="10"/>
              <rect x="660" y="88" width="10" height="14"/><rect x="674" y="88" width="10" height="14"/><rect x="660" y="108" width="24" height="12"/>
              <rect x="872" y="106" width="8" height="12"/><rect x="884" y="106" width="8" height="12"/><rect x="872" y="122" width="20" height="10"/>
              <rect x="1112" y="100" width="8" height="12"/><rect x="1124" y="100" width="8" height="12"/><rect x="1112" y="116" width="20" height="10"/>
              <rect x="1366" y="90" width="10" height="14"/><rect x="1380" y="90" width="10" height="14"/><rect x="1366" y="110" width="24" height="12"/>
            </g>
            <g fill="none" stroke="#6db4ea" stroke-opacity="0.62" stroke-width="2.0">
              <path d="M48 172C188 164 314 164 436 170C588 178 708 188 870 186C1042 184 1188 168 1398 150C1470 144 1538 140 1600 136"/>
              <path d="M122 92C228 124 320 138 438 144C570 150 682 142 818 124C960 104 1108 86 1262 88C1404 90 1498 104 1600 126"/>
              <path d="M210 48L202 220"/>
              <path d="M434 34L438 218"/>
              <path d="M676 40L672 222"/>
              <path d="M926 26L930 220"/>
              <path d="M1188 34L1180 218"/>
              <path d="M1450 42L1454 220"/>
            </g>
            <g fill="#9ed2ff" fill-opacity="0.66">
              <circle cx="208" cy="92" r="6"/>
              <circle cx="436" cy="144" r="5"/>
              <circle cx="818" cy="124" r="6"/>
              <circle cx="1188" cy="88" r="7"/>
              <circle cx="1452" cy="104" r="5"/>
            </g>
            """
        ),
        "foreground": _svg_document(
            """
            <defs>
              <radialGradient id="soft" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#8dcfff" stop-opacity="0.70"/>
                <stop offset="100%" stop-color="#9fcdf2" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="1326" cy="80" r="84" fill="url(#soft)"/>
            <circle cx="1168" cy="52" r="42" fill="url(#soft)"/>
            <circle cx="262" cy="58" r="34" fill="url(#soft)"/>
            <g fill="none" stroke="#0b1a2d" stroke-opacity="0.94" stroke-width="4.2" stroke-linecap="round">
              <path d="M0 174H1600"/>
              <path d="M0 190H1600"/>
              <path d="M84 88V240"/>
              <path d="M224 104V240"/>
              <path d="M444 82V240"/>
              <path d="M656 98V240"/>
              <path d="M936 80V240"/>
              <path d="M1218 96V240"/>
              <path d="M1428 72V240"/>
            </g>
            <g fill="none" stroke="#132b4a" stroke-opacity="0.92" stroke-width="2.2">
              <path d="M84 88L142 66L224 104L284 76L362 96L444 82"/>
              <path d="M936 80L1018 60L1112 84L1218 96L1316 70L1428 72"/>
            </g>
            <rect x="34" y="160" width="248" height="18" rx="9" fill="#07111d" fill-opacity="0.78"/>
            <rect x="992" y="152" width="238" height="20" rx="10" fill="#07111d" fill-opacity="0.76"/>
            """
        ),
        "overlay": _svg_document(
            """
            <defs>
              <linearGradient id="topMask" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
              </linearGradient>
              <linearGradient id="bottomMask" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#07111d" stop-opacity="0.00"/>
                <stop offset="100%" stop-color="#07111d" stop-opacity="0.34"/>
              </linearGradient>
            </defs>
            <rect width="1600" height="82" fill="url(#topMask)"/>
            <rect y="158" width="1600" height="82" fill="url(#bottomMask)"/>
            <g fill="#d7efff" fill-opacity="0.54">
              <circle cx="1226" cy="58" r="5"/>
              <circle cx="1282" cy="70" r="4"/>
              <circle cx="1362" cy="94" r="5"/>
              <circle cx="1428" cy="80" r="4"/>
              <circle cx="256" cy="72" r="4"/>
            </g>
            <path d="M1092 30H1468" stroke="#dbf2ff" stroke-opacity="0.36" stroke-width="1.4"/>
            <path d="M1108 162H1472" stroke="#80c8ff" stroke-opacity="0.18" stroke-width="1.2"/>
            """
        ),
    }


def _preset_warm_layers() -> dict[str, str]:
    return {
        "background": _svg_document(
            """
            <defs>
              <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f6c58a"/>
                <stop offset="38%" stop-color="#f5d8a6"/>
                <stop offset="68%" stop-color="#c9d7ea"/>
                <stop offset="100%" stop-color="#7ea0c8"/>
              </linearGradient>
              <radialGradient id="light" cx="76%" cy="18%" r="56%">
                <stop offset="0%" stop-color="#fff3d7" stop-opacity="0.94"/>
                <stop offset="100%" stop-color="#fff9f0" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <rect width="1600" height="240" fill="url(#bg)"/>
            <rect width="1600" height="240" fill="url(#light)"/>
            <path d="M0 132C164 118 324 120 502 138C678 156 822 176 1014 170C1220 164 1380 132 1600 90V240H0Z" fill="#e7b77f" fill-opacity="0.42"/>
            <path d="M0 182C138 166 276 160 444 166C632 172 760 208 964 210C1180 212 1360 172 1600 126V240H0Z" fill="#d7b07e" fill-opacity="0.88"/>
            <path d="M0 210C184 196 352 190 544 194C742 198 910 220 1122 220C1298 220 1446 206 1600 184V240H0Z" fill="#9aaed0" fill-opacity="0.38"/>
            """
        ),
        "midground": _svg_document(
            """
            <g fill="#4f5f75" fill-opacity="0.92">
              <path d="M0 186L0 150L132 150L132 114L278 114L278 168L418 168L418 126L604 126L604 176L794 176L794 106L984 106L984 164L1178 164L1178 118L1362 118L1362 176L1600 176L1600 240L0 240Z"/>
              <path d="M112 146L196 76L252 76L336 146Z"/>
              <path d="M908 138L996 68L1062 68L1150 138Z"/>
            </g>
            <g fill="#f4dfa8" fill-opacity="0.28">
              <rect x="170" y="132" width="14" height="18"/><rect x="194" y="132" width="14" height="18"/><rect x="218" y="132" width="14" height="18"/>
              <rect x="962" y="122" width="14" height="18"/><rect x="986" y="122" width="14" height="18"/><rect x="1010" y="122" width="14" height="18"/>
              <rect x="1246" y="136" width="12" height="16"/><rect x="1266" y="136" width="12" height="16"/><rect x="1286" y="136" width="12" height="16"/>
            </g>
            <g fill="#506b50" fill-opacity="0.86">
              <circle cx="532" cy="138" r="34"/>
              <circle cx="574" cy="142" r="30"/>
              <circle cx="614" cy="144" r="28"/>
              <circle cx="1412" cy="148" r="34"/>
              <circle cx="1456" cy="150" r="30"/>
              <circle cx="1490" cy="154" r="24"/>
            </g>
            """
        ),
        "foreground": _svg_document(
            """
            <defs>
              <radialGradient id="soft" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ffe5b3" stop-opacity="0.82"/>
                <stop offset="100%" stop-color="#fff4de" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="1278" cy="74" r="78" fill="url(#soft)"/>
            <circle cx="118" cy="62" r="52" fill="url(#soft)"/>
            <g fill="none" stroke="#4a5568" stroke-opacity="0.96" stroke-width="5.2" stroke-linecap="round">
              <path d="M52 102V240"/>
              <path d="M112 88V240"/>
              <path d="M0 194H278"/>
              <path d="M0 210H278"/>
              <path d="M1240 118V240"/>
              <path d="M1328 94V240"/>
              <path d="M1408 106V240"/>
              <path d="M1204 198H1600"/>
              <path d="M1204 214H1600"/>
            </g>
            <g fill="none" stroke="#ba8a63" stroke-opacity="0.56" stroke-width="2.6">
              <path d="M32 84C82 68 122 72 166 96C202 116 232 150 264 188"/>
              <path d="M1180 90C1244 70 1318 74 1394 108C1458 136 1510 168 1562 214"/>
            </g>
            <g fill="#efc4a1" fill-opacity="0.56">
              <circle cx="176" cy="134" r="4"/>
              <circle cx="212" cy="154" r="3"/>
              <circle cx="248" cy="170" r="4"/>
              <circle cx="1324" cy="146" r="4"/>
              <circle cx="1372" cy="164" r="3"/>
            </g>
            """
        ),
        "overlay": _svg_document(
            """
            <defs>
              <linearGradient id="paperTop" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#fff4dd" stop-opacity="0.32"/>
                <stop offset="100%" stop-color="#fffaf1" stop-opacity="0.02"/>
              </linearGradient>
              <linearGradient id="bottomSoft" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#5e7091" stop-opacity="0.00"/>
                <stop offset="100%" stop-color="#5e7091" stop-opacity="0.22"/>
              </linearGradient>
            </defs>
            <rect width="1600" height="84" fill="url(#paperTop)"/>
            <rect y="164" width="1600" height="76" fill="url(#bottomSoft)"/>
            <g fill="#fffaf1" fill-opacity="0.54">
              <circle cx="1312" cy="56" r="5"/>
              <circle cx="1364" cy="82" r="4"/>
              <circle cx="232" cy="54" r="5"/>
              <circle cx="282" cy="76" r="4"/>
            </g>
            <path d="M0 0H1600V240H0Z" fill="none" stroke="#fff8ef" stroke-opacity="0.18" stroke-width="8"/>
            """
        ),
    }


def _preset_glass_layers() -> dict[str, str]:
    return {
        "background": _svg_document(
            """
            <defs>
              <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#eef5fb"/>
                <stop offset="56%" stop-color="#ceddea"/>
                <stop offset="100%" stop-color="#a8bfd6"/>
              </linearGradient>
            </defs>
            <rect width="1600" height="240" fill="url(#bg)"/>
            <path d="M0 186C168 176 326 172 492 178C700 186 856 214 1084 214C1280 214 1426 194 1600 164V240H0Z" fill="#dce8f2" fill-opacity="0.94"/>
            """
        ),
        "midground": _svg_document(
            """
            <defs>
              <radialGradient id="orbA" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.76"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
              </radialGradient>
              <radialGradient id="orbB" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#cfe0f0" stop-opacity="0.76"/>
                <stop offset="100%" stop-color="#d8e7f6" stop-opacity="0"/>
              </radialGradient>
            </defs>
            <circle cx="1180" cy="78" r="82" fill="url(#orbA)"/>
            <circle cx="1322" cy="56" r="56" fill="url(#orbB)"/>
            <circle cx="286" cy="72" r="66" fill="url(#orbA)"/>
            <rect x="616" y="34" width="214" height="92" rx="24" fill="#f8fbfe" fill-opacity="0.54" stroke="#ffffff" stroke-opacity="0.72" stroke-width="1.5"/>
            <rect x="930" y="54" width="154" height="72" rx="24" fill="#eef5fb" fill-opacity="0.58" stroke="#ffffff" stroke-opacity="0.58" stroke-width="1.2"/>
            <rect x="1128" y="88" width="188" height="68" rx="24" fill="#f7fbfe" fill-opacity="0.34" stroke="#ffffff" stroke-opacity="0.44" stroke-width="1.2"/>
            """
        ),
        "foreground": _svg_document(
            """
            <path d="M1028 48H1428" stroke="#ffffff" stroke-opacity="0.72" stroke-width="2.6"/>
            <path d="M1068 88H1462" stroke="#ffffff" stroke-opacity="0.42" stroke-width="1.8"/>
            <path d="M168 52H508" stroke="#ffffff" stroke-opacity="0.58" stroke-width="2.2"/>
            <path d="M204 94H544" stroke="#ffffff" stroke-opacity="0.32" stroke-width="1.6"/>
            <rect x="1126" y="108" width="168" height="42" rx="18" fill="#ffffff" fill-opacity="0.24" stroke="#ffffff" stroke-opacity="0.50"/>
            """
        ),
        "overlay": _svg_document(
            """
            <defs>
              <linearGradient id="glassTop" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#ffffff" stop-opacity="0.28"/>
                <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <rect width="1600" height="72" fill="url(#glassTop)"/>
            <g fill="#ffffff" fill-opacity="0.52">
              <circle cx="1268" cy="52" r="4"/>
              <circle cx="1328" cy="66" r="5"/>
              <circle cx="1398" cy="82" r="4"/>
              <circle cx="256" cy="60" r="4"/>
              <circle cx="316" cy="74" r="5"/>
            </g>
            """
        ),
    }


def _cover_crop(image: QImage, target_size: QSize) -> QImage:
    if image.isNull():
        return image
    scaled = image.scaled(
        target_size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    if scaled.size() == target_size:
        return scaled
    x = max(0, (scaled.width() - target_size.width()) // 2)
    y = max(0, (scaled.height() - target_size.height()) // 2)
    return scaled.copy(QRect(x, y, target_size.width(), target_size.height()))


class _LayerAsset:
    def __init__(self, path: Path | None):
        self.path = path
        self._renderer = None
        self._image = QImage()
        self._cache_size = QSize()
        self._cache = QImage()
        if path is None or not path.exists():
            return
        if path.suffix.lower() == ".svg":
            renderer = QSvgRenderer(str(path))
            if renderer.isValid():
                self._renderer = renderer
            return
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if not image.isNull():
            self._image = image

    def is_valid(self) -> bool:
        return self._renderer is not None or not self._image.isNull()

    def render(self, size: QSize) -> QImage:
        if not self.is_valid() or not size.isValid():
            return QImage()
        if self._cache_size == size and not self._cache.isNull():
            return self._cache
        if self._renderer is not None:
            canvas = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
            canvas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(canvas)
            self._renderer.render(painter, QRectF(0.0, 0.0, float(size.width()), float(size.height())))
            painter.end()
            self._cache = canvas
        else:
            self._cache = _cover_crop(self._image, size)
        self._cache_size = QSize(size)
        return self._cache


class ParallaxBannerItem(QQuickPaintedItem):
    assetRootChanged = Signal()
    presetIdChanged = Signal()
    parallaxEnabledChanged = Signal()
    hoverActiveChanged = Signal()
    pointerRatioChanged = Signal()
    smoothedRatioChanged = Signal()
    customBackgroundPathChanged = Signal()
    customMidgroundPathChanged = Signal()
    customForegroundPathChanged = Signal()
    customOverlayPathChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAntialiasing(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self._asset_root = ""
        self._preset_id = default_banner_preset_id()
        self._parallax_enabled = True
        self._hover_active = False
        self._pointer_ratio = 0.0
        self._smoothed_ratio = 0.0
        self._custom_paths = {
            "background": "",
            "midground": "",
            "foreground": "",
            "overlay": "",
        }
        self._layer_assets: dict[str, _LayerAsset] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick_motion)
        self._reload_assets()

    def geometryChange(self, new_geometry, old_geometry) -> None:
        super().geometryChange(new_geometry, old_geometry)
        for asset in self._layer_assets.values():
            asset._cache = QImage()
            asset._cache_size = QSize()
        self.update()

    def _resolved_preset_id(self) -> str:
        return self._preset_id if self._preset_id in banner_preset_ids() else default_banner_preset_id()

    def _resolved_layer_path(self, layer_name: str) -> Path | None:
        custom_text = str(self._custom_paths.get(layer_name, "") or "").strip()
        if custom_text:
            custom_path = Path(custom_text)
            if custom_path.exists():
                return custom_path
        root = Path(self._asset_root) if self._asset_root else None
        if root is None or not root.exists():
            return None
        candidate = preset_layer_path(root, self._resolved_preset_id(), layer_name)
        return candidate if candidate.exists() else None

    def _reload_assets(self) -> None:
        self._layer_assets = {
            layer_name: _LayerAsset(self._resolved_layer_path(layer_name))
            for layer_name in BANNER_LAYER_ORDER
        }
        self.update()

    def _target_ratio(self) -> float:
        if not self._parallax_enabled or not self._hover_active:
            return 0.0
        return self._pointer_ratio

    def _tick_motion(self) -> None:
        target = self._target_ratio()
        next_value = self._smoothed_ratio + (target - self._smoothed_ratio) * 0.16
        if abs(next_value - self._smoothed_ratio) > 0.0005:
            self._smoothed_ratio = next_value
            self.smoothedRatioChanged.emit()
            self.update()
        if abs(self._smoothed_ratio - target) <= 0.0008:
            self._smoothed_ratio = target
            self.smoothedRatioChanged.emit()
            self.update()
            self._timer.stop()

    def _ensure_motion(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def _layer_offset(self, layer_name: str) -> float:
        scale = max(0.84, min(1.18, self.width() / 1600.0))
        offsets = {
            "background": 12.0 * scale,
            "midground": 20.0 * scale,
            "foreground": 30.0 * scale,
            "overlay": 36.0 * scale,
        }
        return offsets[layer_name]

    def paint(self, painter: QPainter) -> None:
        if self.width() <= 2 or self.height() <= 2:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        clip = QPainterPath()
        clip.addRect(QRectF(0.0, 0.0, float(self.width()), float(self.height())))
        painter.setClipPath(clip)

        rect = QRectF(0.0, 0.0, float(self.width()), float(self.height()))
        painter.fillRect(rect, QColor("#e9eef5"))

        for layer_name in BANNER_LAYER_ORDER:
            asset = self._layer_assets.get(layer_name)
            if asset is None or not asset.is_valid():
                continue
            offset = self._layer_offset(layer_name)
            padding = int(max(offset + 48.0, self.width() * 0.10))
            target_size = QSize(int(self.width()) + padding * 2, int(self.height()))
            image = asset.render(target_size)
            if image.isNull():
                continue
            shift = self._smoothed_ratio * offset
            painter.drawImage(
                QRectF(-padding + shift, 0.0, float(target_size.width()), float(target_size.height())),
                image,
            )

    def getAssetRoot(self) -> str:
        return self._asset_root

    def setAssetRoot(self, value: str) -> None:
        next_value = str(value or "")
        if self._asset_root == next_value:
            return
        self._asset_root = next_value
        self.assetRootChanged.emit()
        self._reload_assets()

    def getPresetId(self) -> str:
        return self._resolved_preset_id()

    def setPresetId(self, value: str) -> None:
        next_value = str(value or default_banner_preset_id())
        if self._preset_id == next_value:
            return
        self._preset_id = next_value
        self.presetIdChanged.emit()
        self._reload_assets()

    def getParallaxEnabled(self) -> bool:
        return self._parallax_enabled

    def setParallaxEnabled(self, value: bool) -> None:
        next_value = bool(value)
        if self._parallax_enabled == next_value:
            return
        self._parallax_enabled = next_value
        self.parallaxEnabledChanged.emit()
        self._ensure_motion()

    def getHoverActive(self) -> bool:
        return self._hover_active

    def setHoverActive(self, value: bool) -> None:
        next_value = bool(value)
        if self._hover_active == next_value:
            return
        self._hover_active = next_value
        self.hoverActiveChanged.emit()
        self._ensure_motion()

    def getPointerRatio(self) -> float:
        return self._pointer_ratio

    def setPointerRatio(self, value: float) -> None:
        next_value = max(-1.0, min(1.0, float(value)))
        if abs(self._pointer_ratio - next_value) < 0.0005:
            return
        self._pointer_ratio = next_value
        self.pointerRatioChanged.emit()
        self._ensure_motion()

    def getSmoothedRatio(self) -> float:
        return self._smoothed_ratio

    def _set_custom_path(self, layer_name: str, value: str, signal: Signal) -> None:
        next_value = str(value or "")
        if self._custom_paths[layer_name] == next_value:
            return
        self._custom_paths[layer_name] = next_value
        signal.emit()
        self._reload_assets()

    def getCustomBackgroundPath(self) -> str:
        return self._custom_paths["background"]

    def setCustomBackgroundPath(self, value: str) -> None:
        self._set_custom_path("background", value, self.customBackgroundPathChanged)

    def getCustomMidgroundPath(self) -> str:
        return self._custom_paths["midground"]

    def setCustomMidgroundPath(self, value: str) -> None:
        self._set_custom_path("midground", value, self.customMidgroundPathChanged)

    def getCustomForegroundPath(self) -> str:
        return self._custom_paths["foreground"]

    def setCustomForegroundPath(self, value: str) -> None:
        self._set_custom_path("foreground", value, self.customForegroundPathChanged)

    def getCustomOverlayPath(self) -> str:
        return self._custom_paths["overlay"]

    def setCustomOverlayPath(self, value: str) -> None:
        self._set_custom_path("overlay", value, self.customOverlayPathChanged)

    assetRoot = Property(str, getAssetRoot, setAssetRoot, notify=assetRootChanged)
    presetId = Property(str, getPresetId, setPresetId, notify=presetIdChanged)
    parallaxEnabled = Property(bool, getParallaxEnabled, setParallaxEnabled, notify=parallaxEnabledChanged)
    hoverActive = Property(bool, getHoverActive, setHoverActive, notify=hoverActiveChanged)
    pointerRatio = Property(float, getPointerRatio, setPointerRatio, notify=pointerRatioChanged)
    smoothedRatio = Property(float, getSmoothedRatio, notify=smoothedRatioChanged)
    customBackgroundPath = Property(
        str,
        getCustomBackgroundPath,
        setCustomBackgroundPath,
        notify=customBackgroundPathChanged,
    )
    customMidgroundPath = Property(
        str,
        getCustomMidgroundPath,
        setCustomMidgroundPath,
        notify=customMidgroundPathChanged,
    )
    customForegroundPath = Property(
        str,
        getCustomForegroundPath,
        setCustomForegroundPath,
        notify=customForegroundPathChanged,
    )
    customOverlayPath = Property(
        str,
        getCustomOverlayPath,
        setCustomOverlayPath,
        notify=customOverlayPathChanged,
    )


def register_qml_types() -> None:
    qmlRegisterType(ParallaxBannerItem, "Coyin.Banner", 1, 0, "ParallaxBanner")
