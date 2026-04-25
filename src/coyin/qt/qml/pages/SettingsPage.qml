import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import Coyin.Banner 1.0
import "../components"
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Item {
    id: root
    objectName: "settingsPage"
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property string currentCategory: "appearance"
    property bool suppressSync: false

    readonly property var providerEntries: controller ? controller.providerEntries : []
    readonly property var pluginModel: controller ? controller.pluginModel : null
    readonly property var summaryEntries: controller ? controller.settingsSummaryModel : null
    readonly property var environmentInfo: controller ? controller.environmentInfo : ({})
    readonly property var bannerPresets: controller ? controller.bannerPresetEntries : []
    readonly property var provider: UiDefaults.safeProvider(providerEntries.length > 0 ? providerEntries[0] : UiDefaults.provider())
    readonly property int activePluginCount: controller ? controller.activePluginCount : 0
    readonly property int summaryColumns: root.width > 1500 ? 3 : 1
    readonly property int pluginCount: (root.pluginModel && root.pluginModel.count !== undefined) ? root.pluginModel.count : 0
    readonly property string themeMode: controller ? controller.themeMode : "light"
    readonly property string bannerAssetRoot: controller ? controller.bannerAssetRoot : ""
    readonly property bool bannerParallaxEnabled: controller ? controller.bannerParallaxEnabled : true
    readonly property string bannerPresetId: controller ? controller.bannerPresetId : "preset_academic"
    readonly property string customBannerBackgroundPath: controller ? controller.customBannerBackgroundPath : ""
    readonly property string customBannerMidgroundPath: controller ? controller.customBannerMidgroundPath : ""
    readonly property string customBannerForegroundPath: controller ? controller.customBannerForegroundPath : ""
    readonly property string customBannerOverlayPath: controller ? controller.customBannerOverlayPath : ""
    readonly property var sectionMap: ({
        "appearance": appearanceSection,
        "provider": providerSection,
        "plugins": pluginSection,
        "workspace": workspaceSection,
        "export": exportSection,
        "advanced": advancedSection
    })

    Component.onCompleted: appearanceSection.expanded = true

    function expand(categoryId, targetSection) {
        currentCategory = categoryId
        if (targetSection)
            targetSection.expanded = true
        Qt.callLater(function() {
            if (!targetSection)
                return
            suppressSync = true
            var targetY = rightContent.y + targetSection.y
            contentFlick.contentY = Math.max(0, Math.min(targetY - 12, contentFlick.contentHeight - contentFlick.height))
            syncTimer.restart()
        })
    }

    function syncCurrentCategory() {
        if (suppressSync)
            return
        var pivot = contentFlick.contentY + 36
        var sections = [
            { id: "appearance", item: appearanceSection },
            { id: "provider", item: providerSection },
            { id: "plugins", item: pluginSection },
            { id: "workspace", item: workspaceSection },
            { id: "export", item: exportSection },
            { id: "advanced", item: advancedSection }
        ]
        var nextCategory = currentCategory
        for (var i = 0; i < sections.length; ++i) {
            var candidate = sections[i]
            if (pivot >= candidate.item.y - 8)
                nextCategory = candidate.id
        }
        currentCategory = nextCategory
    }

    function fileLabel(pathValue) {
        var text = String(pathValue || "")
        if (!text.length)
            return "使用当前默认预设"
        var normalized = text.split("\\").join("/")
        var parts = normalized.split("/")
        return parts[parts.length - 1]
    }

    Timer {
        id: syncTimer
        interval: 180
        repeat: false
        onTriggered: root.suppressSync = false
    }

    RowLayout {
        anchors.fill: parent
        spacing: 18

        Rectangle {
            Layout.preferredWidth: 220
            Layout.maximumWidth: 220
            Layout.fillHeight: true
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1

            Column {
                id: navColumn
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                Text {
                    text: "设置分类"
                    color: root.theme.text
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }

                InteractiveChip { theme: root.theme; width: parent.width; text: "外观"; checked: root.currentCategory === "appearance"; onClicked: root.expand("appearance", appearanceSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "模型接口"; checked: root.currentCategory === "provider"; onClicked: root.expand("provider", providerSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "插件"; checked: root.currentCategory === "plugins"; onClicked: root.expand("plugins", pluginSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "工作区 / 数据目录"; checked: root.currentCategory === "workspace"; onClicked: root.expand("workspace", workspaceSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "导出 / 编译"; checked: root.currentCategory === "export"; onClicked: root.expand("export", exportSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "高级 / 调试"; checked: root.currentCategory === "advanced"; onClicked: root.expand("advanced", advancedSection) }

                Item { height: 1; width: 1 }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 6
            color: "transparent"

            Flickable {
                id: contentFlick
                anchors.fill: parent
                contentWidth: width
                contentHeight: rightContent.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                onContentYChanged: root.syncCurrentCategory()

                ScrollBar.vertical: AutoHideScrollBar { theme: root.theme }
                ScrollBar.horizontal: AutoHideScrollBar { theme: root.theme }

                Column {
                    id: rightContent
                    width: contentFlick.width
                    spacing: 18

                    Rectangle {
                        width: parent.width
                        radius: 6
                        color: root.theme.panelRaised
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: summaryColumn.implicitHeight + 30

                        Column {
                            id: summaryColumn
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 12

                            Text {
                                text: "设置总览"
                                color: root.theme.text
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }

                            GridView {
                                id: summaryGrid
                                width: parent.width
                                height: contentHeight
                                implicitHeight: contentHeight
                                interactive: false
                                clip: true
                                cellWidth: root.summaryColumns > 1 ? (width - (root.summaryColumns - 1) * 12) / root.summaryColumns : width
                                cellHeight: 112
                                model: root.summaryEntries

                                delegate: Item {
                                    id: summaryDelegate
                                    required property string title
                                    required property string value
                                    required property string detail
                                    required property string state
                                    readonly property string entryTitle: title || ""
                                    readonly property string entryValue: value || ""
                                    readonly property string entryDetail: detail || ""
                                    readonly property string entryState: state || ""
                                    width: summaryGrid.cellWidth
                                    height: summaryGrid.cellHeight

                                    MetricTile {
                                        anchors.fill: parent
                                        theme: root.theme
                                        label: summaryDelegate.entryTitle
                                        value: summaryDelegate.entryValue
                                        detail: summaryDelegate.entryDetail
                                        tone: summaryDelegate.entryState === "light" || summaryDelegate.entryState === "dark" ? "accent" : "neutral"
                                    }
                                }
                            }
                        }
                    }

                    Column {
                        width: parent.width
                        spacing: 14

                        InteractiveExpander {
                            id: appearanceSection
                            objectName: "appearanceSection"
                            width: parent.width
                            theme: root.theme
                            title: "外观"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "appearance"

                            Row {
                                spacing: 8
                                InfoPill { text: root.themeMode === "light" ? "浅色模式" : "夜间模式"; fillColor: root.theme.accentSurface; borderColor: root.theme.accentOutline; textColor: root.theme.anchor }
                                InfoPill { text: root.bannerParallaxEnabled ? "顶部横幅景深开启" : "顶部横幅景深关闭"; fillColor: root.bannerParallaxEnabled ? root.theme.accentSurface : root.theme.panelInset; borderColor: root.bannerParallaxEnabled ? root.theme.accentOutline : root.theme.border; textColor: root.bannerParallaxEnabled ? root.theme.anchor : root.theme.textMuted }
                                InfoPill { text: root.activePluginCount + " 个插件已启用"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                            }

                            InteractiveButton {
                                theme: root.theme
                                text: root.themeMode === "light" ? "切换到夜间模式" : "切换到浅色模式"
                                onClicked: if (root.controller) root.controller.toggleTheme()
                            }

                            InteractiveExpander {
                                width: parent.width
                                theme: root.theme
                                title: "顶部横幅景深"
                                subtitle: "顶部标题栏与页签栏背后的多层横幅视差背景。"
                                expanded: true

                                Column {
                                    width: parent.width
                                    spacing: 12

                                    InteractiveToggle {
                                        width: parent.width
                                        theme: root.theme
                                        text: "启用顶部横幅景深效果"
                                        description: "关闭后顶部横幅保持静态背景，不再响应鼠标左右视差。"
                                        checked: root.bannerParallaxEnabled
                                        onToggled: function(nextChecked) {
                                            if (root.controller)
                                                root.controller.setBannerParallaxEnabled(nextChecked)
                                        }
                                    }

                                    Column {
                                        width: parent.width
                                        spacing: 8

                                        Text {
                                            text: "默认横幅组合"
                                            color: root.theme.text
                                            font.pixelSize: 13
                                            font.weight: Font.DemiBold
                                        }

                                        Flow {
                                            width: parent.width
                                            spacing: 12

                                            Repeater {
                                                model: root.bannerPresets

                                                delegate: Item {
                                                    readonly property var entry: modelData || ({})
                                                    readonly property bool selectedPreset: root.bannerPresetId === (entry.preset_id || "")
                                                    width: Math.min(216, (parent.width - 12) / 2)
                                                    height: previewColumn.implicitHeight

                                                    Column {
                                                        id: previewColumn
                                                        width: parent.width
                                                        spacing: 8

                                                        Rectangle {
                                                            width: parent.width
                                                            height: 54
                                                            radius: 8
                                                            clip: true
                                                            border.width: 1
                                                            border.color: selectedPreset ? root.theme.accentOutline : root.theme.border
                                                            color: root.theme.panelInset

                                                            ParallaxBanner {
                                                                anchors.fill: parent
                                                                assetRoot: root.bannerAssetRoot
                                                                presetId: entry.preset_id || "preset_academic"
                                                                parallaxEnabled: true
                                                                hoverActive: true
                                                                pointerRatio: selectedPreset ? 0.22 : 0.10
                                                            }

                                                            Rectangle {
                                                                anchors.fill: parent
                                                                color: "transparent"
                                                                border.width: selectedPreset ? 1 : 0
                                                                border.color: root.theme.anchor
                                                                radius: parent.radius
                                                            }
                                                        }

                                                        InteractiveChip {
                                                            theme: root.theme
                                                            width: parent.width
                                                            text: entry.title || ""
                                                            checked: selectedPreset
                                                            onClicked: if (root.controller && entry.preset_id) root.controller.setBannerPreset(entry.preset_id)
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        Text {
                                            width: parent.width
                                            text: "每组预设都由背景层、中景层、前景层和装饰层组成。未上传自定义图层时，会直接使用当前默认组合。"
                                            color: root.theme.textSoft
                                            wrapMode: Text.Wrap
                                            font.pixelSize: 11
                                        }
                                    }

                                    InteractiveExpander {
                                        width: parent.width
                                        theme: root.theme
                                        title: "自定义横幅图层"
                                        subtitle: "可分别上传背景层、中景层、前景层和装饰层；未上传的层自动回退到当前预设。"

                                        Column {
                                            width: parent.width
                                            spacing: 10

                                            RowLayout {
                                                width: parent.width
                                                spacing: 10
                                                Text { Layout.preferredWidth: 96; text: "背景层"; color: root.theme.text; font.weight: Font.DemiBold }
                                                Text { Layout.fillWidth: true; text: root.fileLabel(root.customBannerBackgroundPath); color: root.theme.textMuted; elide: Text.ElideRight }
                                                InteractiveButton { theme: root.theme; text: "上传"; onClicked: if (root.controller) root.controller.chooseCustomBannerLayer("background") }
                                            }

                                            RowLayout {
                                                width: parent.width
                                                spacing: 10
                                                Text { Layout.preferredWidth: 96; text: "中景层"; color: root.theme.text; font.weight: Font.DemiBold }
                                                Text { Layout.fillWidth: true; text: root.fileLabel(root.customBannerMidgroundPath); color: root.theme.textMuted; elide: Text.ElideRight }
                                                InteractiveButton { theme: root.theme; text: "上传"; onClicked: if (root.controller) root.controller.chooseCustomBannerLayer("midground") }
                                            }

                                            RowLayout {
                                                width: parent.width
                                                spacing: 10
                                                Text { Layout.preferredWidth: 96; text: "前景层"; color: root.theme.text; font.weight: Font.DemiBold }
                                                Text { Layout.fillWidth: true; text: root.fileLabel(root.customBannerForegroundPath); color: root.theme.textMuted; elide: Text.ElideRight }
                                                InteractiveButton { theme: root.theme; text: "上传"; onClicked: if (root.controller) root.controller.chooseCustomBannerLayer("foreground") }
                                            }

                                            RowLayout {
                                                width: parent.width
                                                spacing: 10
                                                Text { Layout.preferredWidth: 96; text: "装饰层"; color: root.theme.text; font.weight: Font.DemiBold }
                                                Text { Layout.fillWidth: true; text: root.fileLabel(root.customBannerOverlayPath); color: root.theme.textMuted; elide: Text.ElideRight }
                                                InteractiveButton { theme: root.theme; text: "上传"; onClicked: if (root.controller) root.controller.chooseCustomBannerLayer("overlay") }
                                            }

                                            Row {
                                                spacing: 10
                                                InteractiveButton {
                                                    theme: root.theme
                                                    tone: "danger"
                                                    text: "清除自定义图层"
                                                    onClicked: if (root.controller) root.controller.clearCustomBannerLayers()
                                                }

                                                InfoPill {
                                                    text: "支持 PNG / JPG / JPEG / WEBP"
                                                    fillColor: root.theme.panelInset
                                                    borderColor: root.theme.border
                                                    textColor: root.theme.textMuted
                                                }
                                            }

                                            Text {
                                                width: parent.width
                                                text: "当前保存位置：" + (root.environmentInfo.bannerCustomDir || "")
                                                color: root.theme.textSoft
                                                wrapMode: Text.Wrap
                                                font.pixelSize: 11
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        InteractiveExpander {
                            id: providerSection
                            objectName: "providerSection"
                            width: parent.width
                            theme: root.theme
                            title: "模型接口"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "provider"

                            GridLayout {
                                width: parent.width
                                columns: root.width > 1540 ? 2 : 1
                                columnSpacing: 12
                                rowSpacing: 12

                                InteractiveTextField { id: baseUrlField; theme: root.theme; width: parent.width; placeholderText: "Base URL"; text: root.provider.base_url || "" }
                                InteractiveTextField { id: apiKeyField; theme: root.theme; width: parent.width; placeholderText: "API Key"; echoMode: TextInput.Password; text: root.provider.api_key || "" }
                                InteractiveTextField { id: modelField; theme: root.theme; width: parent.width; placeholderText: "默认模型"; text: root.provider.default_model || "" }
                                InteractiveTextField { id: analysisModelField; theme: root.theme; width: parent.width; placeholderText: "分析模型"; text: root.provider.analysis_model || "" }
                            }

                            Row {
                                spacing: 10
                                InteractiveButton { theme: root.theme; text: "保存配置"; tone: "accent"; onClicked: if (root.controller) root.controller.savePrimaryProvider(baseUrlField.text, apiKeyField.text, modelField.text, analysisModelField.text, true) }
                                InteractiveButton { theme: root.theme; text: "连通性测试"; onClicked: if (root.controller) root.controller.testPrimaryProvider() }
                            }
                        }

                        InteractiveExpander {
                            id: pluginSection
                            objectName: "pluginSection"
                            width: parent.width
                            theme: root.theme
                            title: "插件"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "plugins"

                            ListView {
                                width: parent.width
                                height: contentHeight
                                implicitHeight: contentHeight
                                interactive: false
                                clip: true
                                spacing: 10
                                reuseItems: true
                                model: root.pluginModel

                                delegate: Rectangle {
                                    readonly property bool hasIssue: !!load_error
                                    width: ListView.view.width
                                    radius: 6
                                    color: MotionCore.mixColor(root.theme.panelInset, root.theme.accentSurface, pluginInteraction.frameStrength * 0.16 + pluginInteraction.settleStrength * 0.10)
                                    border.color: hasIssue
                                                  ? MotionCore.mixColor(root.theme.border, root.theme.danger, 0.70)
                                                  : MotionCore.mixColor(root.theme.border, root.theme.accentOutline, pluginInteraction.frameStrength * 0.68 + pluginInteraction.settleStrength * 0.22)
                                    border.width: 1
                                    implicitHeight: pluginColumn.implicitHeight + 22

                                    Behavior on color {
                                        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
                                    }

                                    Behavior on border.color {
                                        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
                                    }

                                    InteractionTracker {
                                        id: pluginInteraction
                                        targetItem: parent
                                        cursorEnabled: false
                                        selected: !!plugin_enabled
                                    }

                                    SignalAccent {
                                        anchors.fill: parent
                                        active: pluginInteraction.settleStrength > 0.16
                                        hovered: pluginInteraction.hovered
                                        pressed: pluginInteraction.pressed
                                        accentColor: root.theme.anchor
                                        neutralColor: root.theme.accentSoft
                                        edge: hasIssue ? "left" : "frame"
                                        radius: 6
                                    }

                                    Column {
                                        id: pluginColumn
                                        anchors.left: parent.left
                                        anchors.leftMargin: 12
                                        anchors.right: parent.right
                                        anchors.rightMargin: 12
                                        anchors.top: parent.top
                                        anchors.topMargin: 10
                                        spacing: 8

                                        RowLayout {
                                            width: parent.width
                                            spacing: 10

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 4

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: (name || "") + "  " + (version || "")
                                                    color: MotionCore.mixColor(root.theme.text, root.theme.anchor, pluginInteraction.textStrength * 0.28 + pluginInteraction.settleStrength * 0.20)
                                                    font.weight: Font.DemiBold
                                                    elide: Text.ElideRight

                                                    Behavior on color {
                                                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                                    }
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: description || ""
                                                    color: MotionCore.mixColor(root.theme.textSoft, root.theme.textMuted, pluginInteraction.textStrength * 0.44)
                                                    wrapMode: Text.Wrap
                                                    maximumLineCount: 2
                                                    elide: Text.ElideRight

                                                    Behavior on color {
                                                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                                    }
                                                }
                                            }

                                            InteractiveButton {
                                                theme: root.theme
                                                text: plugin_enabled ? "停用" : "启用"
                                                selected: !!plugin_enabled
                                                onClicked: if (root.controller) root.controller.setPluginEnabled(plugin_id, !plugin_enabled)
                                            }
                                        }

                                        Row {
                                            spacing: 8
                                            InfoPill { text: builtin ? "内置" : "外部"; fillColor: root.theme.panelRaised; borderColor: root.theme.border; textColor: root.theme.textMuted }
                                            InfoPill { text: state_label || ""; fillColor: plugin_enabled ? root.theme.accentSurface : root.theme.panelRaised; borderColor: plugin_enabled ? root.theme.accentOutline : root.theme.border; textColor: plugin_enabled ? root.theme.anchor : root.theme.textMuted }
                                        }

                                        Text {
                                            text: (author || "") + "  ·  " + (capabilities || "")
                                            color: MotionCore.mixColor(root.theme.textMuted, root.theme.textSoft, pluginInteraction.textStrength * 0.34)
                                            width: parent.width
                                            elide: Text.ElideRight
                                        }

                                        Text {
                                            visible: hasIssue
                                            text: load_error || ""
                                            color: root.theme.danger
                                            width: parent.width
                                            wrapMode: Text.Wrap
                                        }
                                    }
                                }
                            }

                            Text {
                                visible: root.pluginCount === 0
                                width: parent.width
                                text: "当前没有可展示的插件条目。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }

                        InteractiveExpander {
                            id: workspaceSection
                            objectName: "workspaceSection"
                            width: parent.width
                            theme: root.theme
                            title: "工作区 / 数据目录"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "workspace"

                            Text { width: parent.width; text: "工作区文件：" + (root.environmentInfo.workspaceFile || ""); color: root.theme.text; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "草稿目录：" + (root.environmentInfo.draftsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "下载目录：" + (root.environmentInfo.downloadsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "LaTeX 目录：" + (root.environmentInfo.latexDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "插件目录：" + (root.environmentInfo.pluginsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "默认横幅目录：" + (root.environmentInfo.bannerPresetDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "自定义横幅目录：" + (root.environmentInfo.bannerCustomDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                        }

                        InteractiveExpander {
                            id: exportSection
                            objectName: "exportSection"
                            width: parent.width
                            theme: root.theme
                            title: "导出 / 编译"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "export"

                            Row {
                                spacing: 8
                                InfoPill { text: (root.environmentInfo.templateCount || 0) + " 个模板"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                                InfoPill { text: root.environmentInfo.xelatexAvailable ? "XeLaTeX 可用" : "XeLaTeX 未就绪"; fillColor: root.environmentInfo.xelatexAvailable ? root.theme.accentSurface : root.theme.note; borderColor: root.environmentInfo.xelatexAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.xelatexAvailable ? root.theme.anchor : root.theme.warning }
                            }

                            Text {
                                width: parent.width
                                text: "这里只显示当前状态。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }

                        InteractiveExpander {
                            id: advancedSection
                            objectName: "advancedSection"
                            width: parent.width
                            theme: root.theme
                            title: "高级 / 调试"
                            subtitle: ""
                            onToggled: if (expanded) root.currentCategory = "advanced"

                            Row {
                                spacing: 8
                                InfoPill { text: root.environmentInfo.nativeAvailable ? "Native Bridge 已接入" : "Native Bridge 未接入"; fillColor: root.environmentInfo.nativeAvailable ? root.theme.accentSurface : root.theme.panelInset; borderColor: root.environmentInfo.nativeAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.nativeAvailable ? root.theme.anchor : root.theme.textMuted }
                            }

                            Text {
                                width: parent.width
                                text: "查看桥接与环境状态。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }
        }
    }
}
