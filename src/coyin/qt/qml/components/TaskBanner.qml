import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore
import "."

Rectangle {
    id: root
    property var task: ({})
    property var theme: UiDefaults.theme()
    property bool compact: false

    readonly property string phase: task.phase || "idle"
    readonly property bool busy: !!task.busy
    readonly property color stripeColor: phase === "error"
        ? theme.danger
        : (busy ? theme.anchor : (phase === "ready" ? theme.accent : theme.borderStrong))

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: bannerHover.hovered
        pressedInput: false
        focusedInput: false
        busyInput: root.busy
        selectedInput: phase === "ready"
    }

    radius: 6
    color: MotionCore.mixColor(busy ? theme.accentPanel : theme.panelInset, phase === "error" ? theme.note : theme.accentSurface, interaction.engageProgress * (phase === "error" ? 0.16 : 0.09))
    border.color: MotionCore.mixColor(busy ? theme.accentOutline : theme.border, root.stripeColor, 0.14 + interaction.engageProgress * 0.10)
    border.width: 1
    implicitHeight: bannerColumn.implicitHeight + 28

    HoverHandler {
        id: bannerHover
        enabled: root.visible
    }

    Behavior on color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Behavior on border.color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4 + interaction.engageProgress * 1.5
        color: root.stripeColor

        Behavior on width {
            NumberAnimation { duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }
    }

    SignalAccent {
        anchors.fill: parent
        active: root.busy
        hovered: false
        pressed: false
        accentColor: root.stripeColor
        neutralColor: theme.accentSoft
        edge: "frame"
        radius: root.radius
    }

    Column {
        id: bannerColumn
        anchors.fill: parent
        anchors.margins: 14
        anchors.leftMargin: 18
        spacing: root.compact ? 6 : 8

        RowLayout {
            width: parent.width
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: task.title || "任务状态"
                color: theme.text
                font.pixelSize: 14
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }

            InfoPill {
                text: phase === "refreshing"
                    ? "刷新中"
                    : (phase === "loading"
                        ? "运行中"
                        : (phase === "ready"
                            ? "已完成"
                            : (phase === "empty"
                                ? "空态"
                                : (phase === "error" ? "异常" : "待命"))))
                fillColor: root.busy ? theme.accentSurface : theme.panel
                borderColor: root.busy ? theme.accentOutline : theme.border
                textColor: phase === "error" ? theme.danger : (root.busy ? theme.anchor : theme.textMuted)
            }

            Item { Layout.fillWidth: false; width: 1; height: 1 }
        }

        Text {
            width: parent.width
            text: task.summary || ""
            color: theme.text
            wrapMode: Text.Wrap
            font.pixelSize: root.compact ? 12 : 13
        }

        Text {
            visible: !!task.detail
            width: parent.width
            text: task.detail || ""
            color: theme.textMuted
            wrapMode: Text.Wrap
            font.pixelSize: 11
        }

        Text {
            visible: !!task.hint && !root.compact
            width: parent.width
            text: task.hint || ""
            color: theme.textSoft
            wrapMode: Text.Wrap
            font.pixelSize: 11
        }

        LoadingStrip {
            visible: root.busy
            width: Math.min(parent.width, 220)
            tint: root.stripeColor
            base: MotionCore.mixColor(theme.accentSoft, theme.panelFocus, interaction.busyProgress * 0.20)
            frameColor: theme.panelRaised
            borderColor: theme.border
            running: visible
        }
    }
}
