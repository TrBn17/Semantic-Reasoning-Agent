export type Language = "en" | "vi";

export type Dictionary = {
  appName: string;
  languageLabel: string;
  languageOptions: {
    english: string;
    vietnamese: string;
  };
  workspaceControlPlane: string;
  common: {
    cancel: string;
    save: string;
    close: string;
    delete: string;
    edit: string;
    create: string;
    upload: string;
    loading: string;
    error: string;
    success: string;
    warning: string;
    entities: string;
    relations: string;
    published: string;
    search: string;
    results: string;
    result: string;
    noMatches: string;
  };
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
  workspaceSwitcher: {
    label: string;
    switchWorkspace: string;
    createWorkspace: string;
    createTitle: string;
    createDescription: string;
    workspaceIdLabel: string;
    workspaceIdPlaceholder: string;
    workspaceIdHint: string;
    createAndSwitch: string;
    toasts: {
      idRequired: string;
      switchedTo: string;
    };
  };
  documents: {
    uploadTitle: string;
    uploadDescription: string;
    fileLabel: string;
    pdfModeLabel: string;
    pdfModeFast: string;
    pdfModeAccurate: string;
    outputFormatLabel: string;
    outputFormatMarkdown: string;
    outputFormatHtml: string;
    outputFormatJson: string;
    outputFormatChunks: string;
    outputFormatHint: string;
    extractImagesLabel: string;
    extractImagesHint: string;
    tagsLabel: string;
    tagsPlaceholder: string;
    uploading: string;
    uploadSelected: string;
    selectedFiles: string;
    emptyTable: string;
    loadError: string;
    table: {
      title: string;
      type: string;
      status: string;
      chunks: string;
      updated: string;
    };
    toasts: {
      selectFile: string;
      uploadSuccess: string;
      uploadPartial: string;
      uploadFailed: string;
    };
  };
  chat: {
    useRetrieval: string;
    topK: string;
    documentIds: string;
    documentIdsPlaceholder: string;
    messagePlaceholder: string;
    send: string;
  };
  retrieval: {
    title: string;
    description: string;
    queryLabel: string;
    queryPlaceholder: string;
    topKLabel: string;
    docIdsLabel: string;
    docIdsPlaceholder: string;
    searchFailed: string;
    noMatches: string;
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
      addProvider: string;
      editProvider: string;
      activeProviders: string;
      configured: string;
      notConfigured: string;
      allActive: string;
      noActive: string;
      toggleHint: string;
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
      noOverrides: string;
      allTasksOverridden: string;
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
      providerOff: string;
      missingFieldsPrefix: string;
      notSupportedByProvider: string;
      readyToUse: string;
      notSupportedByModel: string;
      allTasksConfigured: string;
      noGlobalRouting: string;
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
    common: {
      cancel: "Cancel",
      save: "Save",
      close: "Close",
      delete: "Delete",
      edit: "Edit",
      create: "Create",
      upload: "Upload",
      loading: "Loading",
      error: "Error",
      success: "Success",
      warning: "Warning",
      entities: "entities",
      relations: "relations",
      published: "published",
      search: "Search",
      results: "results",
      result: "result",
      noMatches: "No matches.",
    },
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
    workspaceSwitcher: {
      label: "Workspace",
      switchWorkspace: "Switch Workspace",
      createWorkspace: "Create Workspace",
      createTitle: "Create New Workspace",
      createDescription: "Each workspace has its own independent ontology, documents, and settings.",
      workspaceIdLabel: "Workspace ID (slug)",
      workspaceIdPlaceholder: "e.g. project-x, financial-analysis",
      workspaceIdHint: "Lowercase, no spaces. This will be used in Neo4j and SQL.",
      createAndSwitch: "Create & Switch",
      toasts: {
        idRequired: "Workspace ID is required",
        switchedTo: "Switched to workspace:",
      },
    },
    documents: {
      uploadTitle: "Upload a document",
      uploadDescription: "PDF, DOCX, XLSX, or CSV. Parsed and indexed by the ingestion worker.",
      fileLabel: "File",
      pdfModeLabel: "PDF mode",
      pdfModeFast: "Fast",
      pdfModeAccurate: "Accurate",
      outputFormatLabel: "Output format",
      outputFormatMarkdown: "Markdown",
      outputFormatHtml: "HTML",
      outputFormatJson: "JSON",
      outputFormatChunks: "Chunks",
      outputFormatHint: "Choose how Marker should render the source before chunking and artifact export.",
      extractImagesLabel: "Extract embedded images",
      extractImagesHint: "Store image artifacts when Marker detects figures or inline visuals.",
      tagsLabel: "Tags (comma separated)",
      tagsPlaceholder: "e.g. policy,2025",
      uploading: "Uploading...",
      uploadSelected: "Upload selected",
      selectedFiles: "Selected {count} file(s)",
      emptyTable: "No documents yet. Upload a PDF, DOCX, or XLSX to start.",
      loadError: "Failed to load documents.",
      table: {
        title: "Title",
        type: "Type",
        status: "Status",
        chunks: "Chunks",
        updated: "Updated",
      },
      toasts: {
        selectFile: "Select at least one file to upload",
        uploadSuccess: "Uploaded {count} file(s)",
        uploadPartial: "Uploaded {uploaded} file(s), failed {failed}: {filenames}",
        uploadFailed: "Upload failed: {reason}",
      },
    },
    chat: {
      useRetrieval: "Use retrieval (RAG)",
      topK: "top_k",
      documentIds: "document_ids (comma sep)",
      documentIdsPlaceholder: "optional",
      messagePlaceholder: "Type a message. Shift+Enter for newline.",
      send: "Send",
    },
    retrieval: {
      title: "Retrieval playground",
      description: "Search across indexed document chunks. Useful for validating that ingestion parsed the document the way you expected.",
      queryLabel: "Query",
      queryPlaceholder: "Ask a question or paste keywords",
      topKLabel: "top_k",
      docIdsLabel: "document_ids (comma sep)",
      docIdsPlaceholder: "optional",
      searchFailed: "Search failed: {reason}",
      noMatches: "No matches. Try a different query or upload more documents.",
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
        addProvider: "Add Provider",
        editProvider: "Edit Setup",
        activeProviders: "Active Providers",
        configured: "Configured",
        notConfigured: "Needs Setup",
        allActive: "All providers active",
        noActive: "No active providers. Click the plus button to add one.",
        toggleHint: "Toggle this provider on or off",
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
        noOverrides: "No task overrides defined. This profile will use system defaults.",
        allTasksOverridden: "All tasks overridden",
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
        providerOff: "Provider is disabled.",
        missingFieldsPrefix: "Missing required fields:",
        notSupportedByProvider: "Models from this provider are currently unavailable for tasks.",
        readyToUse: "Ready to use.",
        notSupportedByModel: "This model is currently unavailable for tasks.",
        allTasksConfigured: "All tasks configured",
        noGlobalRouting: "No global task routing defined. Click the plus button to configure a task.",
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
    common: {
      cancel: "Hủy",
      save: "Lưu",
      close: "Đóng",
      delete: "Xóa",
      edit: "Sửa",
      create: "Tạo",
      upload: "Tải lên",
      loading: "Đang tải",
      error: "Lỗi",
      success: "Thành công",
      warning: "Cảnh báo",
      entities: "thực thể",
      relations: "quan hệ",
      published: "đã xuất bản",
      search: "Tìm kiếm",
      results: "kết quả",
      result: "kết quả",
      noMatches: "Không tìm thấy kết quả.",
    },
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
    workspaceSwitcher: {
      label: "Không gian làm việc",
      switchWorkspace: "Chuyển Workspace",
      createWorkspace: "Tạo Workspace",
      createTitle: "Tạo Workspace Mới",
      createDescription: "Mỗi workspace có ontology, tài liệu và cài đặt độc lập riêng.",
      workspaceIdLabel: "Workspace ID (slug)",
      workspaceIdPlaceholder: "ví dụ: project-x, phan-tich-tai-chinh",
      workspaceIdHint: "Viết thường, không dấu, không khoảng cách. Dùng cho Neo4j và SQL.",
      createAndSwitch: "Tạo & Chuyển",
      toasts: {
        idRequired: "Yêu cầu nhập Workspace ID",
        switchedTo: "Đã chuyển sang workspace:",
      },
    },
    documents: {
      uploadTitle: "Tải tài liệu lên",
      uploadDescription: "Hỗ trợ PDF, DOCX, XLSX, hoặc CSV. Tài liệu sẽ được xử lý bởi worker.",
      fileLabel: "Tệp tin",
      pdfModeLabel: "Chế độ PDF",
      pdfModeFast: "Nhanh",
      pdfModeAccurate: "Chính xác",
      outputFormatLabel: "Định dạng đầu ra",
      outputFormatMarkdown: "Markdown",
      outputFormatHtml: "HTML",
      outputFormatJson: "JSON",
      outputFormatChunks: "Chunks",
      outputFormatHint: "Chọn cách Marker render tài liệu trước khi chunk và xuất artifact.",
      extractImagesLabel: "Trích xuất ảnh nhúng",
      extractImagesHint: "Lưu artifact ảnh khi Marker phát hiện hình hoặc nội dung trực quan trong tài liệu.",
      tagsLabel: "Thẻ (cách nhau bởi dấu phẩy)",
      tagsPlaceholder: "ví dụ: chính sách, 2025",
      uploading: "Đang tải lên...",
      uploadSelected: "Tải lên tệp đã chọn",
      selectedFiles: "Đã chọn {count} tệp",
      emptyTable: "Chưa có tài liệu nào. Hãy tải lên PDF, DOCX, hoặc XLSX để bắt đầu.",
      loadError: "Không thể tải danh sách tài liệu.",
      table: {
        title: "Tiêu đề",
        type: "Loại",
        status: "Trạng thái",
        chunks: "Đoạn",
        updated: "Cập nhật",
      },
      toasts: {
        selectFile: "Vui lòng chọn ít nhất một tệp để tải lên",
        uploadSuccess: "Đã tải lên {count} tệp",
        uploadPartial: "Đã tải lên {uploaded} tệp, thất bại {failed}: {filenames}",
        uploadFailed: "Tải lên thất bại: {reason}",
      },
    },
    chat: {
      useRetrieval: "Sử dụng truy xuất (RAG)",
      topK: "top_k",
      documentIds: "ID tài liệu (cách nhau bởi dấu phẩy)",
      documentIdsPlaceholder: "không bắt buộc",
      messagePlaceholder: "Nhập tin nhắn. Shift+Enter để xuống dòng.",
      send: "Gửi",
    },
    retrieval: {
      title: "Sân chơi truy xuất",
      description: "Tìm kiếm trên các đoạn tài liệu đã được lập chỉ mục. Hữu ích để kiểm tra xem việc nạp tài liệu có đúng như bạn mong đợi hay không.",
      queryLabel: "Truy vấn",
      queryPlaceholder: "Đặt câu hỏi hoặc dán từ khóa",
      topKLabel: "top_k",
      docIdsLabel: "ID tài liệu (cách nhau bởi dấu phẩy)",
      docIdsPlaceholder: "không bắt buộc",
      searchFailed: "Tìm kiếm thất bại: {reason}",
      noMatches: "Không tìm thấy kết quả. Hãy thử truy vấn khác hoặc tải lên thêm tài liệu.",
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
        addProvider: "Thêm Provider",
        editProvider: "Sửa cấu hình",
        activeProviders: "Provider đang hoạt động",
        configured: "Đã cấu hình",
        notConfigured: "Cần thiết lập",
        allActive: "Tất cả provider đã hoạt động",
        noActive: "Chưa có provider hoạt động. Nhấn dấu cộng để thêm.",
        toggleHint: "Bật hoặc tắt provider này",
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
        noOverrides: "Không có cấu hình đè cho tác vụ. Hồ sơ này sẽ dùng mặc định hệ thống.",
        allTasksOverridden: "Tất cả tác vụ đã được cấu hình đè",
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
        providerOff: "Provider đang tắt.",
        missingFieldsPrefix: "Thiếu trường bắt buộc:",
        notSupportedByProvider: "Model từ provider này hiện chưa dùng được cho tác vụ.",
        readyToUse: "Sẵn sàng sử dụng.",
        notSupportedByModel: "Model này hiện chưa dùng được cho tác vụ.",
        allTasksConfigured: "Tất cả tác vụ đã được cấu hình",
        noGlobalRouting: "Chưa có routing tác vụ toàn cục. Nhấn dấu cộng để cấu hình.",
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
