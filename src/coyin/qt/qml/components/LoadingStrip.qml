import QtQuick
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults

Item {
    id: root
    property color tint: UiDefaults.theme().accent
    property color base: UiDefaults.theme().accentSoft
    property bool running: true

    implicitWidth: 220
    implicitHeight: 14

    ShimmerRail {
        anchors.fill: parent
        running: root.running
        accentColor: root.tint
        baseColor: root.base
        radius: 4
    }
}
