import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Control {
    id: root
    property string text: ""
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool checked: false
    property bool busy: false
    property color markColor: "transparent"
    signal clicked

    readonly property var motion: MotionCore.tokens(root.theme)
    readonly property color fillColor: MotionCore.mixColor(MotionCore.chipFill(root.theme, root.checked, root.enabled, interaction.hovered, interaction.pressed, interaction.focused), root.theme.accentSurface, interaction.accentStrength * (root.checked ? 0.18 : 0.10))
    readonly property color borderColor: MotionCore.mixColor(MotionCore.chipBorder(root.theme, root.checked, root.enabled, interaction.hovered, interaction.pressed, interaction.focused), root.theme.anchor, interaction.frameStrength * 0.24)
    readonly property color textColor: MotionCore.mixColor(MotionCore.chipText(root.theme, root.checked, root.enabled, interaction.hovered, interaction.pressed, interaction.focused), root.theme.text, interaction.textStrength * 0.38)
    readonly property real surfaceScale: MotionCore.surfaceScale(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, interaction.settleStrength, false)

    hoverEnabled: enabled && visible
    focusPolicy: Qt.TabFocus
    leftPadding: mark.visible ? 10 : 12
    rightPadding: 12
    topPadding: 5
    bottomPadding: 5
    implicitHeight: 30
    implicitWidth: Math.max(88, label.implicitWidth + (mark.visible ? 28 : 18) + (busy ? 14 : 0))

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: clickHandler.active
        focusedInput: root.activeFocus
        busyInput: root.busy
        selectedInput: root.checked
    }

    background: Rectangle {
        radius: root.motion.radiusSmall
        color: root.fillColor
        border.color: root.borderColor
        border.width: 1
        opacity: root.enabled ? 1.0 : root.motion.disabledOpacity
        scale: root.surfaceScale
        transformOrigin: Item.Center

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }

        Behavior on scale {
            NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: interaction.pressed
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "frame"
            radius: root.motion.radiusSmall
        }
    }

    contentItem: Item {
        implicitWidth: (mark.visible ? mark.width + 8 : 0) + label.implicitWidth + (busyDot.visible ? busyDot.width + 8 : 0)
        implicitHeight: Math.max(label.implicitHeight, Math.max(mark.visible ? mark.height : 0, busyDot.visible ? busyDot.height : 0))
        scale: root.surfaceScale
        transformOrigin: Item.Center

        transform: Translate {
            y: MotionCore.weightedShift(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, root.theme, false)

            Behavior on y {
                NumberAnimation { duration: MotionCore.duration("immediate", root.theme); easing.type: Easing.OutCubic }
            }
        }

        Behavior on scale {
            NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }

        Rectangle {
            id: mark
            visible: root.markColor !== "transparent"
            width: 8
            height: 8
            anchors.left: parent.left
            anchors.leftMargin: 0
            anchors.verticalCenter: parent.verticalCenter
            radius: 2
            color: root.markColor
        }

        Text {
            id: label
            anchors.left: mark.visible ? mark.right : parent.left
            anchors.leftMargin: mark.visible ? 8 : 0
            anchors.right: busyDot.visible ? busyDot.left : parent.right
            anchors.rightMargin: busyDot.visible ? 8 : 0
            anchors.verticalCenter: parent.verticalCenter
            text: root.busy ? (root.text + "…") : root.text
            color: root.textColor
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 12
            font.weight: root.checked ? Font.DemiBold : Font.Medium
            horizontalAlignment: mark.visible ? Text.AlignLeft : Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
        }

        Rectangle {
            id: busyDot
            visible: root.busy
            width: 6
            height: 6
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            radius: 2
            color: MotionCore.mixColor(root.theme.accentOutline, root.theme.anchor, 0.40 + interaction.settleStrength * 0.40)
        }
    }

    HoverHandler {
        id: hoverHandler
        enabled: root.enabled && root.visible && !root.busy
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        id: clickHandler
        enabled: root.enabled && root.visible && !root.busy
        onTapped: root.clicked()
    }
}
