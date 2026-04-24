import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "." 
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Control {
    id: root
    property string heading: ""
    property string detail: ""
    property string badge: ""
    property string actionLabel: ""
    property string mark: ""
    property string tone: "neutral"
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    signal triggered

    readonly property bool accentTone: tone === "accent"
    readonly property var motion: MotionCore.tokens(root.theme)
    readonly property color fillColor: MotionCore.mixColor(MotionCore.cardFill(theme, root.accentTone, root.enabled, interaction.hovered, interaction.pressed, false), theme.accentSurface, interaction.accentStrength * (root.accentTone ? 0.12 : 0.18))
    readonly property color borderColor: MotionCore.mixColor(MotionCore.cardBorder(theme, root.accentTone, root.enabled, interaction.hovered, interaction.pressed, false), theme.anchor, interaction.frameStrength * 0.28)
    readonly property real surfaceScale: MotionCore.surfaceScale(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, interaction.settleStrength, true)

    hoverEnabled: enabled && visible
    focusPolicy: Qt.TabFocus
    leftPadding: 16
    rightPadding: 16
    topPadding: 14
    bottomPadding: 14
    implicitHeight: Math.max(140, contentColumn.implicitHeight + 28)

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: triggerHandler.active
        focusedInput: root.activeFocus
        busyInput: false
        selectedInput: false
    }

    background: Rectangle {
        radius: root.motion.radiusMedium
        color: root.fillColor
        border.color: root.borderColor
        border.width: 1
        opacity: root.enabled ? 1.0 : root.motion.disabledOpacity
        scale: root.surfaceScale
        transformOrigin: Item.Center

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
        }

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
        }

        Behavior on scale {
            NumberAnimation { duration: MotionCore.duration("panel", root.theme); easing.type: Easing.OutCubic }
        }

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: interaction.pressed
            accentColor: theme.anchor
            neutralColor: theme.accentSoft
            edge: "frame"
            radius: root.motion.radiusMedium
        }
    }

    contentItem: Item {
        implicitWidth: contentColumn.implicitWidth
        implicitHeight: contentColumn.implicitHeight
        scale: root.surfaceScale
        transformOrigin: Item.Center

        transform: Translate {
            y: MotionCore.weightedShift(interaction.hoverProgress, interaction.focusProgress, interaction.pressProgress, root.theme, true)

            Behavior on y {
                NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
            }
        }

        Behavior on scale {
            NumberAnimation { duration: MotionCore.duration("panel", root.theme); easing.type: Easing.OutCubic }
        }

        Column {
            id: contentColumn
            width: parent.width
            spacing: 10

            Row {
                id: chromeRow
                width: parent.width
                spacing: 8

                Rectangle {
                    width: 40
                    height: 24
                    radius: root.motion.radiusSmall
                    color: root.accentTone
                        ? MotionCore.mixColor(theme.accentOutline, theme.anchor, 0.72 + interaction.settleStrength * 0.28)
                        : MotionCore.mixColor(theme.accentSurface, theme.panelFocus, interaction.accentStrength * 0.55)
                    border.color: theme.accentOutline
                    border.width: 1

                    Behavior on color {
                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: root.mark
                        color: root.accentTone ? theme.panelRaised : theme.anchor
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }
                }

                InfoPill {
                    visible: root.badge.length > 0
                    text: root.badge
                    fillColor: root.accentTone ? theme.panelRaised : theme.panelInset
                    borderColor: root.accentTone ? theme.accentOutline : theme.border
                    textColor: root.accentTone ? theme.anchor : theme.textMuted
                }
            }

            Text {
                id: headingText
                text: root.heading
                color: root.accentTone ? theme.anchor : theme.text
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 15
                font.weight: Font.DemiBold
                elide: Text.ElideRight
                width: parent.width
                opacity: root.enabled ? 1.0 : root.motion.disabledOpacity

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }

            Text {
                id: detailText
                text: root.detail
                visible: text.length > 0
                color: theme.textMuted
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 11
                width: parent.width
                wrapMode: Text.Wrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            Row {
                id: actionRow
                width: parent.width
                spacing: 6
                visible: root.actionLabel.length > 0

                Text {
                    text: root.actionLabel
                    color: MotionCore.mixColor(root.accentTone ? theme.anchor : theme.textSoft, theme.anchor, interaction.textStrength * 0.50)
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 11
                    font.weight: Font.Medium

                    Behavior on color {
                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                    }
                }

                Text {
                    text: "›"
                    color: MotionCore.mixColor(root.accentTone ? theme.anchor : theme.textSoft, theme.anchor, interaction.textStrength * 0.50)
                    font.pixelSize: 11
                    font.weight: Font.DemiBold

                    Behavior on color {
                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                    }
                }
            }
        }
    }

    HoverHandler {
        id: hoverHandler
        enabled: root.enabled && root.visible
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        id: triggerHandler
        enabled: root.enabled && root.visible
        onTapped: root.triggered()
    }
}
