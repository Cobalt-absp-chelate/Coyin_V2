import QtQuick
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Item {
    id: root
    property color tint: UiDefaults.theme().accent
    property color base: UiDefaults.theme().accentSoft
    property color frameColor: UiDefaults.theme().panelRaised
    property color borderColor: UiDefaults.theme().border
    property bool running: true

    implicitWidth: 220
    implicitHeight: 14

    Rectangle {
        anchors.fill: parent
        radius: 4
        color: MotionCore.mixColor(root.frameColor, root.base, root.running ? 0.62 : 0.35)
        border.color: MotionCore.mixColor(root.borderColor, root.tint, root.running ? 0.18 : 0.06)
        border.width: 1

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("fast") }
        }

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("fast") }
        }

        ShimmerRail {
            anchors.fill: parent
            anchors.margins: 1
            running: root.running
            accentColor: root.tint
            baseColor: MotionCore.mixColor(root.base, root.tint, root.running ? 0.08 : 0.02)
            radius: 3
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            radius: 1
            color: MotionCore.mixColor(Qt.rgba(1, 1, 1, 0.0), root.tint, root.running ? 0.14 : 0.05)
            opacity: 0.9
        }
    }
}
