.pragma library

function _loadJson(relativePath) {
    try {
        var xhr = new XMLHttpRequest()
        xhr.open("GET", Qt.resolvedUrl(relativePath), false)
        xhr.send()
        if ((xhr.status === 0 || xhr.status === 200) && xhr.responseText)
            return JSON.parse(xhr.responseText)
    } catch (error) {
    }
    return null
}

function _defaultTheme() {
    return {
        mode: "light",
        background: "#e7ebf0",
        workspace: "#f1f4f8",
        workspaceTint: "#e8eef5",
        chrome: "#f7f9fb",
        chromeAlt: "#e9eef4",
        panel: "#fbfcfe",
        panelAlt: "#f3f6fa",
        panelRaised: "#ffffff",
        panelInset: "#ecf1f6",
        panelHover: "#eef4fa",
        panelFocus: "#e4edf7",
        text: "#122033",
        textMuted: "#4c5d70",
        textSoft: "#708195",
        border: "#d5dde8",
        borderStrong: "#b9c6d8",
        accent: "#1f5a84",
        anchor: "#164e74",
        accentHover: "#2d6b98",
        accentSoft: "#dbe8f3",
        accentSurface: "#edf4fa",
        accentPanel: "#e4edf7",
        accentOutline: "#88a6c1",
        selection: "#e9dfc9",
        success: "#506d5e",
        warning: "#8b6c3d",
        danger: "#8c5656",
        note: "#efe6d4",
        shadow: "#10243712",
        motionProfile: "measured",
        radiusSmall: 4,
        radiusMedium: 6,
        radiusLarge: 8,
        durationImmediate: 72,
        durationFast: 110,
        durationNormal: 170,
        durationSlow: 220,
        durationPanel: 190,
        durationPage: 210,
        hoverShift: -0.45,
        pressShift: 0.65,
        cardHoverShift: -0.8,
        cardPressShift: 0.45,
        pageOffset: 10,
        disabledOpacity: 0.72
    }
}

function _defaultShellSchema() {
    return {
        primaryPages: [
            { page_id: "home", title: "工作台", short: "工" },
            { page_id: "library", title: "资料库", short: "库" },
            { page_id: "search", title: "搜索", short: "搜" },
            { page_id: "analysis", title: "分析", short: "析" }
        ],
        utilityPages: [
            { page_id: "settings", title: "设置" }
        ]
    }
}

function theme() {
    return _loadJson("../../../../assets/config/themes/light.json") || _defaultTheme()
}

function safeTheme(value) {
    var fallback = theme()
    if (!value)
        return fallback
    var merged = {}
    for (var key in fallback)
        merged[key] = fallback[key]
    for (var item in value)
        merged[item] = value[item]
    return merged
}

function shellPageEntries() {
    var schema = _loadJson("../../../../assets/config/shell_schema.json") || _defaultShellSchema()
    return schema.primaryPages || _defaultShellSchema().primaryPages
}

function shellState() {
    var schema = _loadJson("../../../../assets/config/shell_schema.json") || _defaultShellSchema()
    return {
        currentTitle: "工作台",
        currentSubtitle: "",
        currentPage: "home",
        currentIndex: 0,
        primaryPageEntries: shellPageEntries(),
        utilityPageEntries: schema.utilityPages || _defaultShellSchema().utilityPages
    }
}

function homeOverview() {
    return {
        total_documents: 0,
        pdf_documents: 0,
        draft_documents: 0,
        analysis_reports: 0,
        notes: 0,
        plugins: 0
    }
}

function provider() {
    return {
        provider_id: "",
        name: "",
        base_url: "",
        api_key: "",
        default_model: "",
        analysis_model: "",
        assistant_model: "",
        translation_model: "",
        active: false
    }
}

function safeProvider(value) {
    var fallback = provider()
    if (!value)
        return fallback
    var merged = {}
    for (var key in fallback)
        merged[key] = fallback[key]
    for (var item in value)
        merged[item] = value[item]
    return merged
}

function libraryFilterState() {
    return {
        query: "",
        group_id: "all",
        kind: "all",
        recent_only: false,
        visible_count: 0,
        total_count: 0
    }
}

function analysis() {
    return {
        report_id: "",
        document_id: "",
        title: "",
        created_at: "",
        summary: "",
        contributions: [],
        experiments: [],
        method_steps: [],
        risks: [],
        comparisons: [],
        comparison_items: [],
        reading_note: "",
        latex_snippet: "",
        field_items: [],
        field_count: 0,
        experiment_count: 0,
        comparison_count: 0
    }
}

function safeArray(value) {
    return value ? value : []
}

function safeObject(value, fallback) {
    return value ? value : fallback
}
