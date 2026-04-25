import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "."
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Control {
    id: root

    property string text: ""
    property string description: ""
    property bool checked: false
    property bool busy: false
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())

    signal toggled(bool checked)

    readonly property var motion: MotionCore.tokens(root.theme)
    readonly property color fillColor: MotionCore.mixColor(
        root.checked ? root.theme.accentPanel : root.theme.panelRaised,
        root.theme.accentSurface,
        interaction.frameStrength * 0.18 + interaction.settleStrength * 0.14
    )
    readonly property color borderColor: MotionCore.mixColor(
        root.checked ? root.theme.accentOutline : root.theme.border,
        root.theme.anchor,
        interaction.frameStrength * 0.24 + interaction.settleStrength * 0.12
    )

    hoverEnabled: enabled && visible
    focusPolicy: Qt.TabFocus
    leftPadding: 14
    rightPadding: 14
    topPadding: 10
    bottomPadding: 10
    implicitWidth: 260
    implicitHeight: Math.max(44, contentRow.implicitHeight + 20)

    InteractionTracker {
        id: interaction
        targetItem: root
        tapEnabled: true
        busy: root.busy
        selected: root.checked
        focusedInput: root.activeFocus
        onTapped: root.toggled(!root.checked)
    }

    background: Rectangle {
        radius: root.motion.radiusMedium
        color: root.fillColor
        border.color: root.borderColor
        border.width: 1
        opacity: root.enabled ? 1.0 : root.motion.disabledOpacity

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
        }

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
        }

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: interaction.pressed
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "frame"
            radius: root.motion.radiusMedium
        }
    }

    contentItem: RowLayout {
        id: contentRow
        spacing: 12

        ColumnLayout {
            Layout.fillWidth: true
            spacing: descriptionLabel.visible ? 3 : 0

            Text {
                text: root.text
                color: MotionCore.mixColor(root.theme.text, root.theme.anchor, interaction.textStrength * 0.26 + interaction.settleStrength * 0.18)
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 13
                font.weight: Font.DemiBold
                elide: Text.ElideRight

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }

            Text {
                id: descriptionLabel
                visible: root.description.length > 0
                text: root.description
                color: root.theme.textSoft
                font.pixelSize: 11
                wrapMode: Text.Wrap
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }

        Item {
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 44
            implicitHeight: 24

            Rectangle {
                anchors.fill: parent
                radius: height / 2
                color: MotionCore.mixColor(
                    root.checked ? root.theme.anchor : root.theme.panelInset,
                    root.theme.accentOutline,
                    interaction.frameStrength * 0.22 + interaction.settleStrength * 0.18
                )
                border.color: root.checked ? root.theme.anchor : root.theme.borderStrong
                border.width: 1

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }

                Behavior on border.color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }

            Rectangle {
                width: 18
                height: 18
                radius: 9
                y: 3
                x: root.checked ? 23 : 3
                color: root.checked ? root.theme.panelRaised : root.theme.panelRaised
                border.color: root.checked ? root.theme.anchor : root.theme.border
                border.width: 1

                Behavior on x {
                    NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
                }

                Behavior on border.color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }
        }
    }
}
