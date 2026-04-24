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
    property string tone: "neutral"
    property bool selected: false
    property bool busy: false
    signal clicked

    readonly property var motion: MotionCore.tokens(root.theme)
    readonly property color baseFillColor: MotionCore.buttonFill(root.theme, root.tone, root.selected, root.enabled, interaction.hovered, interaction.pressed, interaction.focused)
    readonly property color fillColor: MotionCore.mixColor(baseFillColor, root.tone === "danger" ? root.theme.note : root.theme.accentSurface, interaction.accentStrength * (root.selected ? 0.20 : 0.16))
    readonly property color baseBorderColor: MotionCore.buttonBorder(root.theme, root.tone, root.selected, root.enabled, interaction.hovered, interaction.pressed, interaction.focused)
    readonly property color borderColor: MotionCore.mixColor(baseBorderColor, root.tone === "danger" ? root.theme.danger : root.theme.anchor, interaction.frameStrength * 0.28)
    readonly property color textColor: MotionCore.mixColor(MotionCore.buttonText(root.theme, root.tone, root.selected, root.enabled, interaction.hovered, interaction.pressed, interaction.focused), root.theme.text, interaction.textStrength * 0.42)
    readonly property real surfaceScale: MotionCore.surfaceScale(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, interaction.settleStrength, false)

    hoverEnabled: enabled && visible
    focusPolicy: Qt.TabFocus
    implicitHeight: 34
    implicitWidth: Math.max(92, label.implicitWidth + 28 + (busy ? 18 : 0))

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: clickHandler.active
        focusedInput: root.activeFocus
        busyInput: root.busy
        selectedInput: root.selected
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

        Behavior on opacity {
            NumberAnimation { duration: MotionCore.duration("immediate", root.theme) }
        }

        Behavior on scale {
            NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: interaction.pressed
            accentColor: root.tone === "danger" ? root.theme.danger : root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "frame"
            radius: root.motion.radiusSmall
        }
    }

    contentItem: Item {
        implicitWidth: row.implicitWidth
        implicitHeight: row.implicitHeight
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

        RowLayout {
            id: row
            anchors.fill: parent
            spacing: 8

            Rectangle {
                visible: root.busy
                Layout.preferredWidth: 8
                Layout.preferredHeight: 8
                radius: 2
                color: MotionCore.mixColor(root.theme.accentOutline, root.theme.anchor, 0.45 + interaction.settleStrength * 0.55)

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }

            Text {
                id: label
                Layout.fillWidth: true
                text: root.busy ? (root.text + "…") : root.text
                color: root.textColor
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 12
                font.weight: root.selected ? Font.DemiBold : Font.Medium
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }
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
