export type Language = "en" | "vi";

export type Dictionary = {
  appName: string;
  languageLabel: string;
  languageOptions: {
    english: string;
    vietnamese: string;
  };
  workspaceControlPlane: string;
  nav: {
    work: string;
    knowledge: string;
    automation: string;
    outputs: string;
    admin: string;
    home: string;
    ask: string;
    documents: string;
    evidence: string;
    ontology: string;
    graph: string;
    workflows: string;
    tools: string;
    connectors: string;
    artifacts: string;
    settings: string;
  };
  home: {
    title: string;
    subtitle: string;
    quickActions: {
      ask: { title: string; description: string };
      documents: { title: string; description: string };
      evidence: { title: string; description: string };
      ontology: { title: string; description: string };
    };
    sections: {
      recentDocuments: string;
      ontologyBuilds: string;
      publishedGraph: string;
      recentConversations: string;
      viewAll: string;
    };
    empty: {
      documents: string;
      builds: string;
      graph: string;
      conversations: string;
    };
    openGraphExplorer: string;
    tasks: {
      title: string;
      badge: string;
      description: string;
    };
  };
  settingsPage: {
    title: string;
    description: string;
  };
  agentsSettings: {
    picker: {
      providerPlaceholder: string;
      allProviders: string;
      searchModelPlaceholder: string;
      selectModelPlaceholder: string;
      noModelMatch: string;
      assignmentUnavailable: string;
    };
    toasts: {
      agentSettingsSaved: string;
      saveFailedPrefix: string;
      agentProfileCreated: string;
      createFailedPrefix: string;
      profileSaved: string;
      profileSaveFailedPrefix: string;
      defaultProfileUpdated: string;
      defaultUpdateFailedPrefix: string;
    };
    builder: {
      title: string;
      description: string;
      minimalHint: string;
      refreshCatalog: string;
      saveSettings: string;
      showAdvanced: string;
      hideAdvanced: string;
      workspace: string;
      models: string;
      tasks: string;
    };
    providerEnv: {
      title: string;
      description: string;
      catalogOnly: string;
      enabled: string;
      disabled: string;
      needsSetup: string;
      noAdditionalEnv: string;
      missing: string;
      currentPrefix: string;
      anthropicCatalogHint: string;
    };
    profiles: {
      title: string;
      description: string;
      newProfileNamePlaceholder: string;
      createProfile: string;
      defaultBadge: string;
      noDescription: string;
      noProfileSelected: string;
      panelDescription: string;
      setDefault: string;
      saveProfile: string;
      descriptionLabel: string;
      descriptionPlaceholder: string;
      systemPromptLabel: string;
      systemPromptPlaceholder: string;
      allowChatOverride: string;
    };
    taskRouting: {
      title: string;
      description: string;
      ready: string;
      blocked: string;
      contextPrefix: string;
      structuredOutput: string;
      noStructuredOutput: string;
      streaming: string;
      noStreaming: string;
      noModelSelected: string;
      na: string;
    };
    modelCatalog: {
      title: string;
      description: string;
      allProviders: string;
      catalogOnly: string;
      ready: string;
      blocked: string;
      contextPrefix: string;
      recommendedFor: string;
      noModelsForFilter: string;
      na: string;
    };
  };
  providerModelSelector: {
    loadFailedTitle: string;
    unknownError: string;
    loadingModels: string;
    noModelsForProvider: string;
    selectModelPlaceholder: string;
    contextUnknown: string;
    streaming: string;
    structured: string;
    loading: string;
    noModels: string;
    moreModelsSuffix: string;
  };
};

export const dictionaries: Record<Language, Dictionary> = {
  en: {
    appName: "Semantic Agent",
    languageLabel: "Language",
    languageOptions: {
      english: "English",
      vietnamese: "Vietnamese",
    },
    workspaceControlPlane: "Workspace control plane",
    nav: {
      work: "Work",
      knowledge: "Knowledge",
      automation: "Automation",
      outputs: "Outputs",
      admin: "Admin",
      home: "Home",
      ask: "Ask",
      documents: "Documents",
      evidence: "Evidence",
      ontology: "Ontology",
      graph: "Graph",
      workflows: "Workflows",
      tools: "Tools",
      connectors: "Connectors",
      artifacts: "Artifacts",
      settings: "Settings",
    },
    home: {
      title: "Workspace",
      subtitle: "Knowledge operations cockpit for ask, documents, evidence, ontology, and graph.",
      quickActions: {
        ask: {
          title: "Ask a question",
          description: "Send a grounded query and inspect cited evidence.",
        },
        documents: {
          title: "Upload document",
          description: "Parse and index a document for retrieval and ontology.",
        },
        evidence: {
          title: "Browse evidence",
          description: "Review citations, provenance, and source chunks.",
        },
        ontology: {
          title: "Review ontology builds",
          description: "Approve candidate entities and publish graph versions.",
        },
      },
      sections: {
        recentDocuments: "Recent documents",
        ontologyBuilds: "Ontology builds",
        publishedGraph: "Published graph",
        recentConversations: "Recent conversations",
        viewAll: "View all",
      },
      empty: {
        documents: "No documents yet. Upload one to get started.",
        builds: "No builds yet. Create one from a document.",
        graph: "No published ontology version yet.",
        conversations: "No conversations yet.",
      },
      openGraphExplorer: "Open graph explorer",
      tasks: {
        title: "Tasks & workflows",
        badge: "coming soon",
        description:
          "Task runtime, workflow catalog, and artifact generation will surface here once the backend control plane exposes them.",
      },
    },
    settingsPage: {
      title: "Settings & Agent Profiles",
      description:
        "Set up providers, choose default models, and manage agent profiles in one place.",
    },
    agentsSettings: {
      picker: {
        providerPlaceholder: "Provider",
        allProviders: "All providers",
        searchModelPlaceholder: "Search model name",
        selectModelPlaceholder: "Select model",
        noModelMatch: "No model matched provider/filter. Try another provider or clear search.",
        assignmentUnavailable:
          "Current assignment is no longer available in catalog. Please reselect provider/model.",
      },
      toasts: {
        agentSettingsSaved: "Agent settings saved.",
        saveFailedPrefix: "Save failed:",
        agentProfileCreated: "Agent profile created.",
        createFailedPrefix: "Create failed:",
        profileSaved: "Profile saved.",
        profileSaveFailedPrefix: "Profile save failed:",
        defaultProfileUpdated: "Default profile updated.",
        defaultUpdateFailedPrefix: "Default update failed:",
      },
      builder: {
        title: "Agent Builder Settings",
        description:
          "Start with provider setup and profile defaults. Open Advanced only when needed.",
        minimalHint: "Keep it simple: connect providers, pick defaults, then save. Advanced details are optional.",
        refreshCatalog: "Refresh Catalog",
        saveSettings: "Save Settings",
        showAdvanced: "Show Advanced",
        hideAdvanced: "Hide Advanced",
        workspace: "Workspace",
        models: "Models",
        tasks: "Tasks",
      },
      providerEnv: {
        title: "Provider Setup",
        description:
          "Add the required key or URL for each provider. You can edit these values anytime.",
        catalogOnly: "Catalog only",
        enabled: "Enabled",
        disabled: "Disabled",
        needsSetup: "Needs setup",
        noAdditionalEnv: "This provider is ready to use without extra setup.",
        missing: "missing",
        currentPrefix: "Saved:",
        anthropicCatalogHint:
          "If live model sync is unavailable, Claude models are shown from a curated fallback list.",
      },
      profiles: {
        title: "Agent Profiles",
        description:
          "Each profile stores its own prompt and default model behavior.",
        newProfileNamePlaceholder: "New profile name",
        createProfile: "Create Profile",
        defaultBadge: "Default",
        noDescription: "No description",
        noProfileSelected: "No profile selected.",
        panelDescription: "Profile-bound prompt, routing and override policy.",
        setDefault: "Set Default",
        saveProfile: "Save Profile",
        descriptionLabel: "Description",
        descriptionPlaceholder: "What this agent is for",
        systemPromptLabel: "System Prompt",
        systemPromptPlaceholder: "You are an analyst agent...",
        allowChatOverride: "Allow chat model override",
      },
      taskRouting: {
        title: "Task Routing",
        description:
          "Choose a default model for each task.",
        ready: "Ready",
        blocked: "Blocked",
        contextPrefix: "Context",
        structuredOutput: "Structured output",
        noStructuredOutput: "No structured output",
        streaming: "Streaming",
        noStreaming: "No streaming",
        noModelSelected: "No model selected for this task yet.",
        na: "n/a",
      },
      modelCatalog: {
        title: "Model Catalog",
        description:
          "Browse available models by provider.",
        allProviders: "All providers",
        catalogOnly: "Catalog only",
        ready: "Ready",
        blocked: "Blocked",
        contextPrefix: "Context",
        recommendedFor: "Recommended for",
        noModelsForFilter: "No models for this provider filter.",
        na: "n/a",
      },
    },
    providerModelSelector: {
      loadFailedTitle: "Unable to load model list",
      unknownError: "Unknown error",
      loadingModels: "Loading model list...",
      noModelsForProvider: "No models found for this provider. Check your API key configuration.",
      selectModelPlaceholder: "Select model...",
      contextUnknown: "Context unknown",
      streaming: "Streaming",
      structured: "Structured",
      loading: "Loading...",
      noModels: "No models",
      moreModelsSuffix: "more models",
    },
  },
  vi: {
    appName: "Semantic Agent",
    languageLabel: "Ngôn ngữ",
    languageOptions: {
      english: "Tiếng Anh",
      vietnamese: "Tiếng Việt",
    },
    workspaceControlPlane: "Bảng điều khiển workspace",
    nav: {
      work: "Công việc",
      knowledge: "Tri thức",
      automation: "Tự động hóa",
      outputs: "Đầu ra",
      admin: "Quản trị",
      home: "Trang chủ",
      ask: "Hỏi đáp",
      documents: "Tài liệu",
      evidence: "Bằng chứng",
      ontology: "Ontology",
      graph: "Đồ thị",
      workflows: "Luồng công việc",
      tools: "Công cụ",
      connectors: "Kết nối",
      artifacts: "Tài sản",
      settings: "Cài đặt",
    },
    home: {
      title: "Không gian làm việc",
      subtitle: "Bảng điều khiển cho hỏi đáp, tài liệu, bằng chứng, ontology và đồ thị.",
      quickActions: {
        ask: {
          title: "Đặt câu hỏi",
          description: "Gửi truy vấn có căn cứ và xem bằng chứng được trích dẫn.",
        },
        documents: {
          title: "Tải tài liệu lên",
          description: "Phân tích và lập chỉ mục tài liệu cho truy xuất và ontology.",
        },
        evidence: {
          title: "Duyệt bằng chứng",
          description: "Xem lại trích dẫn, nguồn gốc và các đoạn nguồn.",
        },
        ontology: {
          title: "Duyệt build ontology",
          description: "Phê duyệt thực thể ứng viên và xuất bản phiên bản đồ thị.",
        },
      },
      sections: {
        recentDocuments: "Tài liệu gần đây",
        ontologyBuilds: "Các build ontology",
        publishedGraph: "Đồ thị đã xuất bản",
        recentConversations: "Cuộc hội thoại gần đây",
        viewAll: "Xem tất cả",
      },
      empty: {
        documents: "Chưa có tài liệu nào. Hãy tải lên một file để bắt đầu.",
        builds: "Chưa có build nào. Hãy tạo từ một tài liệu.",
        graph: "Chưa có phiên bản ontology đã xuất bản.",
        conversations: "Chưa có cuộc hội thoại nào.",
      },
      openGraphExplorer: "Mở trình xem đồ thị",
      tasks: {
        title: "Tác vụ & luồng công việc",
        badge: "sắp ra mắt",
        description:
          "Khu chạy tác vụ, danh mục workflow và tạo artifact sẽ xuất hiện ở đây khi control plane backend mở ra.",
      },
    },
    settingsPage: {
      title: "Cài đặt & Hồ sơ Agent",
      description:
        "Thiết lập provider, chọn model mặc định và quản lý hồ sơ agent trong một màn hình.",
    },
    agentsSettings: {
      picker: {
        providerPlaceholder: "Provider",
        allProviders: "Tất cả provider",
        searchModelPlaceholder: "Tìm model",
        selectModelPlaceholder: "Chọn model",
        noModelMatch: "Không có model phù hợp bộ lọc. Hãy thử provider khác hoặc xóa từ khóa tìm kiếm.",
        assignmentUnavailable:
          "Cấu hình hiện tại không còn trong catalog. Vui lòng chọn lại provider/model.",
      },
      toasts: {
        agentSettingsSaved: "Đã lưu cài đặt agent.",
        saveFailedPrefix: "Lưu thất bại:",
        agentProfileCreated: "Đã tạo hồ sơ agent.",
        createFailedPrefix: "Tạo thất bại:",
        profileSaved: "Đã lưu hồ sơ.",
        profileSaveFailedPrefix: "Lưu hồ sơ thất bại:",
        defaultProfileUpdated: "Đã cập nhật hồ sơ mặc định.",
        defaultUpdateFailedPrefix: "Cập nhật mặc định thất bại:",
      },
      builder: {
        title: "Cài đặt Agent Builder",
        description:
          "Bắt đầu với thiết lập provider và profile mặc định. Chỉ mở phần nâng cao khi cần.",
        minimalHint: "Ưu tiên đơn giản: kết nối provider, chọn mặc định, rồi lưu. Phần nâng cao là tùy chọn.",
        refreshCatalog: "Làm mới catalog",
        saveSettings: "Lưu cài đặt",
        showAdvanced: "Hiện nâng cao",
        hideAdvanced: "Ẩn nâng cao",
        workspace: "Workspace",
        models: "Models",
        tasks: "Tác vụ",
      },
      providerEnv: {
        title: "Thiết Lập Provider",
        description:
          "Nhập API key hoặc URL cần thiết cho từng provider. Bạn có thể chỉnh sửa bất cứ lúc nào.",
        catalogOnly: "Chỉ catalog",
        enabled: "Bật",
        disabled: "Tắt",
        needsSetup: "Cần thiết lập",
        noAdditionalEnv: "Provider này có thể dùng ngay, không cần thiết lập thêm.",
        missing: "thiếu",
        currentPrefix: "Đã lưu:",
        anthropicCatalogHint:
          "Nếu không đồng bộ được danh sách model trực tiếp, hệ thống sẽ hiển thị danh sách Claude dự phòng.",
      },
      profiles: {
        title: "Hồ Sơ Agent",
        description:
          "Mỗi hồ sơ có prompt riêng và hành vi model mặc định riêng.",
        newProfileNamePlaceholder: "Tên hồ sơ mới",
        createProfile: "Tạo hồ sơ",
        defaultBadge: "Mặc định",
        noDescription: "Không có mô tả",
        noProfileSelected: "Chưa chọn hồ sơ.",
        panelDescription: "Prompt, routing và policy override gắn theo hồ sơ.",
        setDefault: "Đặt mặc định",
        saveProfile: "Lưu hồ sơ",
        descriptionLabel: "Mô tả",
        descriptionPlaceholder: "Hồ sơ này dùng để làm gì",
        systemPromptLabel: "System Prompt",
        systemPromptPlaceholder: "Bạn là một agent phân tích...",
        allowChatOverride: "Cho phép chat override model",
      },
      taskRouting: {
        title: "Task Routing",
        description:
          "Chọn model mặc định cho từng tác vụ.",
        ready: "Sẵn sàng",
        blocked: "Bị chặn",
        contextPrefix: "Context",
        structuredOutput: "Structured output",
        noStructuredOutput: "Không hỗ trợ structured output",
        streaming: "Streaming",
        noStreaming: "Không streaming",
        noModelSelected: "Chưa chọn model cho tác vụ này.",
        na: "n/a",
      },
      modelCatalog: {
        title: "Model Catalog",
        description:
          "Xem các model hiện có theo từng provider.",
        allProviders: "Tất cả provider",
        catalogOnly: "Chỉ catalog",
        ready: "Sẵn sàng",
        blocked: "Bị chặn",
        contextPrefix: "Context",
        recommendedFor: "Khuyến nghị cho",
        noModelsForFilter: "Không có model cho bộ lọc provider này.",
        na: "n/a",
      },
    },
    providerModelSelector: {
      loadFailedTitle: "Không thể tải danh sách model",
      unknownError: "Lỗi không xác định",
      loadingModels: "Đang tải danh sách model...",
      noModelsForProvider: "Không tìm thấy model cho provider này. Hãy kiểm tra cấu hình API key.",
      selectModelPlaceholder: "Chọn model...",
      contextUnknown: "Không rõ context",
      streaming: "Streaming",
      structured: "Structured",
      loading: "Đang tải...",
      noModels: "Không có model",
      moreModelsSuffix: "model khác",
    },
  },
};
