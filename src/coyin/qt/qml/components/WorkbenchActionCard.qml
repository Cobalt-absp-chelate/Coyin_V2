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

    hoverEnabled: true
    focusPolicy: Qt.TabFocus
    implicitHeight: Math.max(116, contentColumn.implicitHeight + 28)

    background: Rectangle {
        radius: MotionCore.tokens().radiusMedium
        color: root.accentTone ? theme.accentPanel : theme.panelRaised
        border.color: root.accentTone ? theme.accentOutline : theme.border
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.7

        SignalAccent {
            anchors.fill: parent
            active: root.activeFocus
            hovered: pressArea.containsMouse
            pressed: pressArea.pressed
            accentColor: theme.anchor
            neutralColor: theme.accentSoft
            edge: "frame"
            radius: MotionCore.tokens().radiusMedium
        }
    }

    contentItem: Column {
        id: contentColumn
        spacing: 10
        leftPadding: 16
        rightPadding: 16
        topPadding: 14
        bottomPadding: 14

        Row {
            width: parent.width
            spacing: 8

            Rectangle {
                width: 40
                height: 24
                radius: MotionCore.tokens().radiusSmall
                color: root.accentTone ? theme.anchor : theme.accentSurface
                border.color: root.accentTone ? theme.accentOutline : theme.accentOutline
                border.width: 1

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
            text: root.heading
            color: root.accentTone ? theme.anchor : theme.text
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 15
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            width: parent.width
            opacity: root.enabled ? 1.0 : 0.72
        }

        Text {
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

        Text {
            text: root.actionLabel
            visible: text.length > 0
            color: root.accentTone ? theme.anchor : theme.textSoft
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 11
            font.weight: Font.Medium
            width: parent.width
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: pressArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.enabled
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.triggered()
    }
}
