import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Item {
    id: root
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property string title: ""
    property string subtitle: ""
    property bool expanded: false
    signal toggled(bool expanded)
    readonly property var motion: MotionCore.tokens(root.theme)

    default property alias sectionContent: bodyColumn.data
    implicitHeight: container.implicitHeight
    readonly property string toggleLabel: root.expanded ? "收起" : "展开"

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: expanderHover.hovered
        pressedInput: expanderTap.active
        focusedInput: false
        busyInput: false
        selectedInput: root.expanded
    }

    Rectangle {
        id: container
        anchors.left: parent.left
        anchors.right: parent.right
        implicitHeight: header.implicitHeight + bodyWrapper.height + 12
        radius: root.motion.radiusMedium
        color: root.theme.panelRaised
        border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, interaction.frameStrength * 0.56 + interaction.settleStrength * 0.36)
        border.width: 1

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }

        Column {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 6

            Rectangle {
                id: header
                width: parent.width
                implicitHeight: Math.max(54, headerRow.implicitHeight + 24)
                radius: root.motion.radiusSmall
                color: MotionCore.mixColor(root.theme.panelInset, MotionCore.mixColor(root.theme.panelHover, root.theme.accentSurface, 0.22 + interaction.settleStrength * 0.18), interaction.frameStrength)
                border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, interaction.frameStrength * 0.68 + interaction.settleStrength * 0.28)
                border.width: 1

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }

                Behavior on border.color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }

                SignalAccent {
                    anchors.fill: parent
                    active: interaction.settleStrength > 0.16
                    hovered: interaction.hovered
                    pressed: interaction.pressed
                    accentColor: root.theme.anchor
                    neutralColor: root.theme.accentSoft
                    edge: "frame"
                    radius: root.motion.radiusSmall
                }

                Item {
                    id: headerRow
                    anchors.fill: parent
                    anchors.margins: 12

                    Column {
                        anchors.left: parent.left
                        anchors.right: toggleText.left
                        anchors.rightMargin: 16
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 3

                        Text {
                            id: titleLabel
                            width: parent.width
                            text: root.title
                            color: MotionCore.mixColor(root.theme.text, root.theme.anchor, interaction.textStrength * 0.42 + interaction.settleStrength * 0.38)
                            font.family: "Microsoft YaHei UI"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight

                            Behavior on color {
                                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                            }
                        }

                        Text {
                            visible: root.subtitle.length > 0
                            width: parent.width
                            text: root.subtitle
                            color: root.theme.textSoft
                            font.pixelSize: 11
                            maximumLineCount: 2
                            elide: Text.ElideRight
                            wrapMode: Text.Wrap
                        }
                    }

                    Text {
                        id: toggleText
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.toggleLabel
                        color: MotionCore.mixColor(root.theme.textMuted, root.theme.anchor, interaction.textStrength * 0.44 + interaction.settleStrength * 0.34)
                        font.pixelSize: 11
                        font.weight: Font.Medium

                        Behavior on color {
                            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                        }
                    }
                }

                HoverHandler {
                    id: expanderHover
                    enabled: root.visible
                    cursorShape: Qt.PointingHandCursor
                }

                TapHandler {
                    id: expanderTap
                    enabled: root.visible
                    onTapped: {
                        root.expanded = !root.expanded
                        root.toggled(root.expanded)
                    }
                }
            }

            Item {
                id: bodyWrapper
                width: parent.width
                clip: true
                height: disclosure.progress * (bodyColumn.implicitHeight + 12)
                visible: disclosure.progress > 0.001
                opacity: 0.76 + disclosure.progress * 0.24

                DisclosureMotion {
                    id: disclosure
                    expanded: root.expanded
                    duration: MotionCore.duration("normal", root.theme)
                }

                Column {
                    id: bodyColumn
                    width: parent.width
                    anchors.top: parent.top
                    anchors.topMargin: 6
                    spacing: 10
                }
            }
        }
    }
}
