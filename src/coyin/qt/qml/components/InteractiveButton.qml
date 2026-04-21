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

    hoverEnabled: enabled
    focusPolicy: Qt.TabFocus
    implicitHeight: 34
    implicitWidth: Math.max(92, label.implicitWidth + 28 + (busy ? 18 : 0))

    background: Rectangle {
        radius: MotionCore.tokens().radiusSmall
        color: MotionCore.buttonFill(root.theme, root.tone, root.selected, root.enabled)
        border.color: MotionCore.buttonBorder(root.theme, root.tone, root.selected, root.enabled)
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.72

        SignalAccent {
            anchors.fill: parent
            active: root.activeFocus || root.selected || root.busy
            hovered: pressArea.containsMouse
            pressed: pressArea.pressed
            accentColor: root.tone === "danger" ? root.theme.danger : root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "frame"
            radius: MotionCore.tokens().radiusSmall
        }
    }

    contentItem: RowLayout {
        spacing: 8

        Rectangle {
            visible: root.busy
            Layout.preferredWidth: 8
            Layout.preferredHeight: 8
            radius: 2
            color: root.theme.anchor
        }

        Text {
            id: label
            Layout.fillWidth: true
            text: root.busy ? (root.text + "…") : root.text
            color: MotionCore.buttonText(root.theme, root.tone, root.selected, root.enabled)
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 12
            font.weight: root.selected ? Font.DemiBold : Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: pressArea
        anchors.fill: parent
        enabled: root.enabled && !root.busy
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
}
