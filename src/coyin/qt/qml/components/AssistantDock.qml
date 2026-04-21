import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "."
import "../support/UiDefaults.js" as UiDefaults

Rectangle {
    id: root
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    readonly property var messages: controller ? controller.assistantMessages : []
    radius: 6
    color: theme.panelRaised
    border.color: theme.border
    border.width: 1
    implicitHeight: dockColumn.implicitHeight + 28

    property bool engaged: inputField.activeFocus || panelHover.containsMouse

    SignalAccent {
        anchors.fill: parent
        active: root.engaged
        hovered: panelHover.containsMouse
        pressed: false
        accentColor: theme.accent
        neutralColor: theme.accentSoft
        edge: "frame"
        radius: 6
    }

    MouseArea {
        id: panelHover
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    Column {
        id: dockColumn
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            width: parent.width
            spacing: 8
            Text {
                text: "助手"
                color: theme.text
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 15
                font.weight: Font.DemiBold
            }
            Item { width: 1; height: 1; Layout.fillWidth: true }
            Text {
                text: root.messages.length > 0 ? root.messages.length + " 条" : "空"
                color: theme.textSoft
                font.pixelSize: 11
            }
        }

        ListView {
            id: assistantView
            width: parent.width
            height: Math.max(110, Math.min(240, contentHeight))
            model: root.messages
            clip: true
            spacing: 8
            delegate: Rectangle {
                width: assistantView.width
                height: textItem.paintedHeight + 18
                radius: 4
                color: modelData.role === "assistant" ? theme.panelInset : theme.accentPanel
                border.color: modelData.role === "assistant" ? theme.border : theme.accentOutline
                border.width: 1
                Text {
                    id: textItem
                    anchors.fill: parent
                    anchors.margins: 10
                    wrapMode: Text.Wrap
                    text: modelData.text
                    color: theme.text
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 12
                }
            }
        }

        Text {
            visible: root.messages.length === 0
            text: "暂无对话"
            color: theme.textSoft
            font.pixelSize: 12
        }

        Rectangle {
            width: parent.width
            height: 40
            radius: 4
            color: theme.panelInset
            border.color: inputField.activeFocus ? theme.accentOutline : theme.border
            border.width: 1
            SignalAccent {
                anchors.fill: parent
                active: inputField.activeFocus
                hovered: inputMouse.containsMouse
                pressed: false
                accentColor: theme.anchor
                neutralColor: theme.accentSoft
                edge: "bottom"
                radius: 4
            }
            MouseArea {
                id: inputMouse
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
            }
            Row {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 6
                InteractiveTextField {
                    id: inputField
                    width: parent.width - sendButton.width - 8
                    theme: root.theme
                    placeholderText: "询问当前操作"
                    onAccepted: {
                        if (controller) controller.askAssistant(text)
                        text = ""
                    }
                }
                InteractiveButton {
                    id: sendButton
                    theme: root.theme
                    text: "发送"
                    onClicked: {
                        if (controller) controller.askAssistant(inputField.text)
                        inputField.text = ""
                    }
                }
            }
        }
    }
}
