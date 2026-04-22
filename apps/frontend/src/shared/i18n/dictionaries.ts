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
    refresh: string;
    accessibility: {
      closeDialog: string;
      closeSheet: string;
      settingsSections: string;
    };
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
    agents: string;
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
    advanced: string;
    retrievalOn: string;
    retrievalOff: string;
    scopedDocs: string;
    sessionToolVisibility: string;
    noIndexedDocuments: string;
    scoped: string;
    allWorkspace: string;
    noContentHint: string;
  };
  conversationList: {
    title: string;
    newConversation: string;
    created: string;
    createFailedPrefix: string;
    loadFailed: string;
    empty: string;
    newConversationTitle: string;
  };
  chatView: {
    conversationFallback: string;
    workspaceRuntime: string;
    emptyTitle: string;
    emptyDescription: string;
    streamingFailed: string;
    sendFailedPrefix: string;
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
  settingsShell: {
    general: { label: string; description: string };
    providers: { label: string; description: string };
    models: { label: string; description: string };
  };
  generalSettings: {
    workspace: {
      title: string;
      description: string;
      nameLabel: string;
      readyProvidersLabel: string;
      readyProvidersDescription: string;
    };
    appearance: {
      title: string;
      description: string;
      languageLabel: string;
      languageDescription: string;
      themeLabel: string;
      themeLoading: string;
      themeAppliedPrefix: string;
      themeOptions: {
        light: string;
        dark: string;
        system: string;
      };
    };
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
  chatRuntimeControls: {
    noProfile: string;
    selectProfile: string;
    searchProviderModel: string;
    selectModel: string;
    sessionOverride: string;
    profileManaged: string;
    agentPrefix: string;
    profileLocksOverride: string;
  };
  pages: {
    agents: { title: string; description: string };
    artifacts: { title: string; description: string };
    ask: {
      newConversationHeading: string;
      description: string;
      workspaceDefault: string;
      newConversationButton: string;
      createFailedPrefix: string;
      newConversationTitle: string;
    };
    connectors: { title: string; description: string };
    documents: { title: string; description: string };
    error: { title: string; tryAgain: string; unexpectedMessage: string };
    ontologyHub: {
      title: string;
      description: string;
      openGraphEditor: string;
      recentBuilds: string;
    };
    ontologyBuilds: { title: string; description: string };
    ontologyReview: { title: string; description: string };
    tasks: { title: string; description: string };
    tools: { title: string; description: string };
    workflows: { title: string; description: string };
  };
  commandPalette: {
    inputPlaceholder: string;
    noResults: string;
    navigationHeading: string;
  };
  graph: {
    title: string;
    subtitle: string;
    modeGraphOnly: string;
    modeSplit: string;
    modeInspector: string;
    refresh: string;
    versionBadge: string;
    entitiesBadge: string;
    relationsBadge: string;
    publishedPrefix: string;
    noPublishedGraph: string;
    searchNodesPlaceholder: string;
    filterTypesHint: string;
    clearFilters: string;
    allTypes: string;
    canvasTitle: string;
    loadFailedPrefix: string;
    emptyState: string;
    emptyCta: string;
    legendTitle: string;
    noEntityTypes: string;
    inspectorTitle: string;
    inspectorEmpty: string;
    aliasesLabel: string;
    noAliases: string;
    sourceDocumentLabel: string;
    connectedEdges: string;
    outgoing: string;
    incoming: string;
    selectNode: string;
    relationSource: string;
    relationTarget: string;
    confidenceLabel: string;
    evidenceLabel: string;
    noEvidence: string;
    zoomIn: string;
    zoomOut: string;
    fitView: string;
    graphitiIndexed: string;
  };
  evidenceUi: {
    title: string;
    description: string;
    searchPlaceholder: string;
    sourcesLabel: string;
    includeOntology: string;
    promoteComingSoon: string;
    emptyState: string;
    previous: string;
    next: string;
    retrievalSource: string;
    documentSource: string;
    ontologyEntitySource: string;
    ontologyRelationSource: string;
    searchFailedPrefix: string;
  };
  evidenceDetail: {
    retrievalCitation: string;
    documentChunk: string;
    ontologyCandidateEntity: string;
    ontologyCandidateRelation: string;
    scorePrefix: string;
    trustPrefix: string;
    snippet: string;
    provenance: string;
    links: string;
    openDocument: string;
    openBuild: string;
    externalSource: string;
  };
  ontologyUi: {
    unknownError: string;
    failedToLoadBuilds: string;
    modelNotRecorded: string;
    unknownProvider: string;
    unknownModel: string;
    filterDocuments: string;
    pickDocument: string;
    pickExtractionModel: string;
    queueing: string;
    startBuild: string;
    buildQueued: string;
    buildFailedPrefix: string;
    newBuild: string;
    runOntologyExtraction: string;
    runOntologyExtractionDescription: string;
    indexedDocument: string;
    extractionModel: string;
    noIndexedDocumentsMatch: string;
  };
  toolsUi: {
    searchPlaceholder: string;
    emptyState: string;
    loadFailedPrefix: string;
    table: {
      tool: string;
      family: string;
      risk: string;
      runtimeTraits: string;
      capabilities: string;
      action: string;
    };
    runtime: {
      streaming: string;
      buffered: string;
      timeoutSuffix: string;
      none: string;
    };
    filters: {
      all: string;
    };
  };
  toolInvoke: {
    invoke: string;
    dialogTitleFallback: string;
    workspaceId: string;
    workspacePlaceholder: string;
    workspaceRequired: string;
    taskType: string;
    argumentsJson: string;
    schemaPrefix: string;
    requiredPrefix: string;
    parseErrorPrefix: string;
    close: string;
    invoking: string;
    invokeTool: string;
    invokeFailedPrefix: string;
    successToast: string;
    partialToast: string;
    failedToast: string;
    hintsPrefix: string;
    tracePrefix: string;
    evidenceSummary: string;
    artifactsLabel: string;
    evidenceLabel: string;
    unknownError: string;
    none: string;
    argumentsMustBeObject: string;
  };
  tasksUi: {
    runTask: string;
    content: string;
    contentPlaceholder: string;
    providerOptional: string;
    modelOptional: string;
    resolving: string;
    resolveTask: string;
    result: string;
    outputPrefix: string;
    taskResolved: string;
    taskFailedPrefix: string;
  };
  citationsDrawer: {
    title: string;
    description: string;
    citationCount: string;
  };
  agentManagement: {
    title: string;
    description: string;
    profilesTitle: string;
    profilesDescription: string;
    newProfilePlaceholder: string;
    create: string;
    noProfiles: string;
    selectProfileHint: string;
    defaultBadge: string;
    noDescription: string;
    identityTitle: string;
    identityDescription: string;
    name: string;
    status: string;
    descriptionLabel: string;
    descriptionPlaceholder: string;
    systemPromptLabel: string;
    systemPromptPlaceholder: string;
    capabilityTitle: string;
    capabilityDescription: string;
    capabilityPreset: string;
    selectPresetPlaceholder: string;
    toolPolicyMode: string;
    policyPreset: string;
    policyAllowlist: string;
    policyBlocklist: string;
    presetSummary: string;
    noPresetSelected: string;
    lanePalette: string;
    lanePaletteHint: string;
    laneAllowed: string;
    laneAllowedHint: string;
    laneBlocked: string;
    laneBlockedHint: string;
    searchToolsPlaceholder: string;
    riskFilter: string;
    riskAll: string;
    riskLow: string;
    riskMedium: string;
    riskHigh: string;
    removeFromLane: string;
    noCatalogTools: string;
    knowledgeTitle: string;
    knowledgeDescription: string;
    newPack: string;
    editKnowledgePack: string;
    createKnowledgePack: string;
    knowledgeDialogDescription: string;
    cancel: string;
    savePack: string;
    packName: string;
    packStatus: string;
    packDescription: string;
    packDocuments: string;
    activeStatus: string;
    archivedStatus: string;
    attachProfile: string;
    linkedDocs: string;
    noPacks: string;
    edit: string;
    evidenceTitle: string;
    evidenceDescription: string;
    modelOnlyFallback: string;
    editingSummary: string;
    setDefault: string;
    saveProfile: string;
    toastKnowledgePackSaved: string;
    toastKnowledgePackSaveFailedPrefix: string;
  };
  ontologyBuild: {
    notFound: string;
    back: string;
    documentLabel: string;
    tabEntities: string;
    tabRelations: string;
    tabSteps: string;
    statEntities: string;
    statPendingEntities: string;
    statRelations: string;
    statPendingRelations: string;
    statExtractionModel: string;
    stepColumnName: string;
    stepColumnStatus: string;
    stepColumnDetail: string;
    stepColumnStarted: string;
    stepColumnFinished: string;
    stepColumnDuration: string;
    noSteps: string;
    stepsProgress: string;
    tableBuild: string;
    tableStatus: string;
    tableDomain: string;
    tableModel: string;
    tableEntities: string;
    tableRelations: string;
    tablePending: string;
    tableUpdated: string;
    statusFilterPlaceholder: string;
    emptyBuildsList: string;
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
      refresh: "Refresh",
      accessibility: {
        closeDialog: "Close dialog",
        closeSheet: "Close panel",
        settingsSections: "Settings sections",
      },
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
      agents: "Agents",
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
      advanced: "Advanced",
      retrievalOn: "Retrieval on",
      retrievalOff: "Retrieval off",
      scopedDocs: "{count} scoped docs",
      sessionToolVisibility: "Session tool visibility",
      noIndexedDocuments: "No indexed documents available yet.",
      scoped: "Scoped",
      allWorkspace: "All-workspace",
      noContentHint: "Ask a question. Enter sends, Shift+Enter adds a newline.",
    },
    conversationList: {
      title: "Conversations",
      newConversation: "New",
      created: "Conversation created",
      createFailedPrefix: "Failed to create:",
      loadFailed: "Failed to load conversations.",
      empty: "No conversations yet. Click New to start.",
      newConversationTitle: "New conversation",
    },
    chatView: {
      conversationFallback: "Conversation",
      workspaceRuntime: "Workspace runtime",
      emptyTitle: "Ask with tools, citations, and graph context",
      emptyDescription:
        "Start with a direct question. Open Advanced when you need document scope, retrieval tuning, or temporary tool toggles.",
      streamingFailed: "Streaming failed",
      sendFailedPrefix: "Failed to send:",
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
        "Manage provider credentials and readiness in one place.",
    },
    settingsShell: {
      general: {
        label: "General",
        description: "Workspace, language, appearance",
      },
      providers: {
        label: "Providers",
        description: "Configure provider access and readiness.",
      },
      models: {
        label: "Models",
        description: "Model catalog from backend",
      },
    },
    generalSettings: {
      workspace: {
        title: "Workspace",
        description: "The workspace currently active for this session.",
        nameLabel: "Workspace name",
        readyProvidersLabel: "Ready providers",
        readyProvidersDescription: "LLM providers currently reporting as ready.",
      },
      appearance: {
        title: "Appearance",
        description: "Pick your language and color theme.",
        languageLabel: "Language",
        languageDescription: "Change the display language across the app.",
        themeLabel: "Theme",
        themeLoading: "Loading...",
        themeAppliedPrefix: "Currently applied:",
        themeOptions: {
          light: "Light",
          dark: "Dark",
          system: "System",
        },
      },
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
    chatRuntimeControls: {
      noProfile: "No profile",
      selectProfile: "Select profile",
      searchProviderModel: "Search provider or model",
      selectModel: "Select model",
      sessionOverride: "Session override",
      profileManaged: "Profile-managed",
      agentPrefix: "Agent",
      profileLocksOverride: "Profile locks model override",
    },
    pages: {
      agents: {
        title: "Agents",
        description:
          "Manage agent profiles, capability presets, tool policy, knowledge packs, and evidence scope.",
      },
      artifacts: {
        title: "Artifacts",
        description:
          "Artifact generation surface is scaffolded and awaiting backend artifact contracts.",
      },
      ask: {
        newConversationHeading: "Start a new conversation",
        description:
          "Pick an agent profile and create a chat. Model routing will come from that profile or the workspace default.",
        workspaceDefault: "Workspace default",
        newConversationButton: "New conversation",
        createFailedPrefix: "Failed to create:",
        newConversationTitle: "New conversation",
      },
      connectors: {
        title: "Connectors",
        description: "Connector control plane is scaffolded and waiting for connector APIs.",
      },
      documents: {
        title: "Documents",
        description:
          "Upload files for ingestion. Indexed chunks become available for retrieval and ontology extraction.",
      },
      error: {
        title: "Something went wrong",
        tryAgain: "Try again",
        unexpectedMessage: "Unexpected application error.",
      },
      ontologyHub: {
        title: "Ontology pipeline",
        description:
          "Move from indexed documents to extracted candidates, review, and published graph versions.",
        openGraphEditor: "Open Graph Editor",
        recentBuilds: "Recent builds",
      },
      ontologyBuilds: {
        title: "Ontology builds",
        description:
          "Each build extracts candidate entities and relations from one document. Review and publish to promote them into the graph.",
      },
      ontologyReview: {
        title: "Review queue",
        description: "All pending candidates across builds in this workspace.",
      },
      tasks: {
        title: "Tasks",
        description: "Resolve ad-hoc tasks with the public task runtime endpoint.",
      },
      tools: {
        title: "Admin / Debug Tools",
        description:
          "Internal diagnostics for the tool registry and direct tool invocation. This route is no longer part of the primary product workflow.",
      },
      workflows: {
        title: "Workflows",
        description: "Inspect registered workflows and execute supported entries.",
      },
    },
    commandPalette: {
      inputPlaceholder: "Type a command or search...",
      noResults: "No results found.",
      navigationHeading: "Navigation",
    },
    graph: {
      title: "Graph workbench",
      subtitle: "Published ontology, schema mix, and evidence-backed relation inspection.",
      modeGraphOnly: "Graph only",
      modeSplit: "Split view",
      modeInspector: "Inspector",
      refresh: "Refresh",
      versionBadge: "Version",
      entitiesBadge: "entities",
      relationsBadge: "relations",
      publishedPrefix: "Published",
      noPublishedGraph: "No published graph",
      searchNodesPlaceholder: "Search nodes",
      filterTypesHint: "Entity types",
      clearFilters: "Clear",
      allTypes: "All types",
      canvasTitle: "Canvas",
      loadFailedPrefix: "Failed to load graph:",
      emptyState:
        "No published ontology version yet. Approve a build, publish it, then reopen the graph.",
      emptyCta: "Open ontology builds",
      legendTitle: "Legend",
      noEntityTypes: "No entity types available yet.",
      inspectorTitle: "Inspector",
      inspectorEmpty: "Select a node or relation to inspect evidence, aliases, and connection context.",
      aliasesLabel: "Aliases",
      noAliases: "No aliases recorded",
      sourceDocumentLabel: "Source document",
      connectedEdges: "Connections",
      outgoing: "Outgoing",
      incoming: "Incoming",
      selectNode: "Focus in graph",
      relationSource: "Source",
      relationTarget: "Target",
      confidenceLabel: "Confidence",
      evidenceLabel: "Evidence",
      noEvidence: "No evidence snippet stored",
      zoomIn: "Zoom in",
      zoomOut: "Zoom out",
      fitView: "Fit",
      graphitiIndexed: "Graphiti indexed",
    },
    evidenceUi: {
      title: "Evidence",
      description: "Search retrieval citations and ontology candidate provenance side by side.",
      searchPlaceholder: "Search indexed chunks...",
      sourcesLabel: "Sources",
      includeOntology: "Include ontology candidates (latest build)",
      promoteComingSoon: "promote: coming soon",
      emptyState: "Run a search or enable ontology candidates to populate evidence.",
      previous: "Prev",
      next: "Next",
      retrievalSource: "Retrieval",
      documentSource: "Document",
      ontologyEntitySource: "Ontology entity",
      ontologyRelationSource: "Ontology relation",
      searchFailedPrefix: "Search failed:",
    },
    evidenceDetail: {
      retrievalCitation: "Retrieval citation",
      documentChunk: "Document chunk",
      ontologyCandidateEntity: "Ontology candidate entity",
      ontologyCandidateRelation: "Ontology candidate relation",
      scorePrefix: "score",
      trustPrefix: "trust",
      snippet: "Snippet",
      provenance: "Provenance",
      links: "Links",
      openDocument: "Open document",
      openBuild: "Open build",
      externalSource: "External source",
    },
    agentManagement: {
      title: "Agent Management",
      description:
        "Manage profiles, capability presets, tool policy, knowledge packs, and evidence scope from a single control plane.",
      profilesTitle: "Profiles",
      profilesDescription: "Create profiles here. Provider credentials belong in `/settings`.",
      newProfilePlaceholder: "New profile name",
      create: "Create",
      noProfiles:
        "No profiles yet. Create one to define capability preset, tool policy, and knowledge scope.",
      selectProfileHint: "Select a profile to edit identity, capability, knowledge scope, and evidence policy.",
      defaultBadge: "Default",
      noDescription: "No description",
      identityTitle: "Identity",
      identityDescription: "Core agent identity and prompt contract.",
      name: "Name",
      status: "Status",
      descriptionLabel: "Description",
      descriptionPlaceholder: "What this agent is for",
      systemPromptLabel: "System prompt",
      systemPromptPlaceholder: "You are an analyst agent...",
      capabilityTitle: "Capability",
      capabilityDescription: "Select the preset first, then narrow tool access inside that preset.",
      capabilityPreset: "Capability preset",
      selectPresetPlaceholder: "Select preset",
      toolPolicyMode: "Tool policy mode",
      policyPreset: "Preset",
      policyAllowlist: "Allowlist",
      policyBlocklist: "Blocklist",
      presetSummary: "Preset summary",
      noPresetSelected: "No preset selected",
      lanePalette: "Tool palette",
      lanePaletteHint: "Drag tools into Allowed or Blocked. Search and risk filters narrow the list.",
      laneAllowed: "Allowed tools",
      laneAllowedHint: "Order defines preference; drag to reorder.",
      laneBlocked: "Blocked tools",
      laneBlockedHint: "These tools will not run for this profile (when policy applies).",
      searchToolsPlaceholder: "Search tools…",
      riskFilter: "Risk",
      riskAll: "All",
      riskLow: "Low",
      riskMedium: "Medium",
      riskHigh: "High",
      removeFromLane: "Remove",
      noCatalogTools: "No tool catalog entries matched this preset yet.",
      knowledgeTitle: "Knowledge Scope",
      knowledgeDescription: "Select packs for the profile and create or edit packs inline.",
      newPack: "New pack",
      editKnowledgePack: "Edit knowledge pack",
      createKnowledgePack: "Create knowledge pack",
      knowledgeDialogDescription: "Knowledge packs stay inside the `/agents` workflow.",
      cancel: "Cancel",
      savePack: "Save knowledge pack",
      packName: "Name",
      packStatus: "Status",
      packDescription: "Description",
      packDocuments: "Documents",
      activeStatus: "Active",
      archivedStatus: "Archived",
      attachProfile: "Attach to this profile",
      linkedDocs: "linked documents",
      noPacks: "No knowledge packs yet. Create one here and attach documents before assigning it to a profile.",
      edit: "Edit",
      evidenceTitle: "Evidence Policy",
      evidenceDescription: "Control which evidence sources the profile may rely on.",
      modelOnlyFallback: "Allow model-only fallback when policy permits",
      editingSummary: "Editing {name} with {preset} and {scope}.",
      setDefault: "Set default",
      saveProfile: "Save profile",
      toastKnowledgePackSaved: "Knowledge pack saved.",
      toastKnowledgePackSaveFailedPrefix: "Knowledge pack save failed:",
    },
    ontologyBuild: {
      notFound: "Build not found.",
      back: "Back",
      documentLabel: "Document",
      tabEntities: "Entities",
      tabRelations: "Relations",
      tabSteps: "Steps",
      statEntities: "Entities",
      statPendingEntities: "Pending entities",
      statRelations: "Relations",
      statPendingRelations: "Pending relations",
      statExtractionModel: "Extraction model",
      stepColumnName: "Step",
      stepColumnStatus: "Status",
      stepColumnDetail: "Detail",
      stepColumnStarted: "Started",
      stepColumnFinished: "Finished",
      stepColumnDuration: "Duration",
      noSteps: "No steps recorded yet.",
      stepsProgress: "{done} of {total} steps finished",
      tableBuild: "Build",
      tableStatus: "Status",
      tableDomain: "Domain",
      tableModel: "Model",
      tableEntities: "Entities",
      tableRelations: "Relations",
      tablePending: "Pending",
      tableUpdated: "Updated",
      statusFilterPlaceholder: "status or all",
      emptyBuildsList: "No ontology builds yet.",
    },
    ontologyUi: {
      unknownError: "Unknown error",
      failedToLoadBuilds: "Failed to load builds.",
      modelNotRecorded: "model not recorded",
      unknownProvider: "unknown",
      unknownModel: "unknown",
      filterDocuments: "Filter documents",
      pickDocument: "Pick a document",
      pickExtractionModel: "Pick an extraction model",
      queueing: "Queueing...",
      startBuild: "Start build",
      buildQueued: "Ontology build queued",
      buildFailedPrefix: "Build failed:",
      newBuild: "New build",
      runOntologyExtraction: "Run ontology extraction",
      runOntologyExtractionDescription:
        "Choose the indexed document and the extraction model, then queue a reviewable build.",
      indexedDocument: "Indexed document",
      extractionModel: "Extraction model",
      noIndexedDocumentsMatch: "No indexed documents match that filter.",
    },
    toolsUi: {
      searchPlaceholder: "Search tools, families, or capabilities",
      emptyState: "No tools matched the current filters.",
      loadFailedPrefix: "Failed to load tools:",
      table: {
        tool: "Tool",
        family: "Family",
        risk: "Risk",
        runtimeTraits: "Runtime traits",
        capabilities: "Capabilities",
        action: "Action",
      },
      runtime: {
        streaming: "Streaming",
        buffered: "Buffered",
        timeoutSuffix: "s timeout",
        none: "none",
      },
      filters: {
        all: "all",
      },
    },
    toolInvoke: {
      invoke: "Invoke",
      dialogTitleFallback: "Invoke tool",
      workspaceId: "Workspace ID",
      workspacePlaceholder: "workspace",
      workspaceRequired: "Workspace is required.",
      taskType: "Task type",
      argumentsJson: "Arguments (JSON)",
      schemaPrefix: "schema:",
      requiredPrefix: "required:",
      parseErrorPrefix: "JSON parse error:",
      close: "Close",
      invoking: "Invoking...",
      invokeTool: "Invoke tool",
      invokeFailedPrefix: "Invoke failed:",
      successToast: "{tool} succeeded - {evidence} evidence, {latency}ms",
      partialToast: "{tool} partial - hints: {hints}",
      failedToast: "{tool} failed - {code}: {message}",
      hintsPrefix: "hints:",
      tracePrefix: "trace",
      evidenceSummary: "{evidence} evidence",
      artifactsLabel: "artifacts",
      evidenceLabel: "evidence",
      unknownError: "unknown",
      none: "none",
      argumentsMustBeObject: "arguments must be a JSON object",
    },
    tasksUi: {
      runTask: "Run task",
      content: "Content",
      contentPlaceholder: "Describe the task to resolve",
      providerOptional: "Provider (optional)",
      modelOptional: "Model (optional)",
      resolving: "Resolving...",
      resolveTask: "Resolve task",
      result: "Result",
      outputPrefix: "output",
      taskResolved: "Task resolved.",
      taskFailedPrefix: "Task failed:",
    },
    citationsDrawer: {
      title: "Citations",
      description: "Evidence chunks used to compose the reply.",
      citationCount: "{count} citation{suffix}",
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
      refresh: "Làm mới",
      accessibility: {
        closeDialog: "Đóng hộp thoại",
        closeSheet: "Đóng bảng",
        settingsSections: "Các mục cài đặt",
      },
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
      agents: "Agents",
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
      advanced: "Nâng cao",
      retrievalOn: "Bật truy xuất",
      retrievalOff: "Tắt truy xuất",
      scopedDocs: "{count} tài liệu giới hạn",
      sessionToolVisibility: "Bật tắt công cụ theo phiên",
      noIndexedDocuments: "Chưa có tài liệu đã lập chỉ mục.",
      scoped: "Đã giới hạn",
      allWorkspace: "Toàn workspace",
      noContentHint: "Nhập câu hỏi. Enter để gửi, Shift+Enter để xuống dòng.",
    },
    conversationList: {
      title: "Cuộc hội thoại",
      newConversation: "Mới",
      created: "Đã tạo hội thoại",
      createFailedPrefix: "Tạo thất bại:",
      loadFailed: "Không thể tải danh sách hội thoại.",
      empty: "Chưa có hội thoại. Nhấn Mới để bắt đầu.",
      newConversationTitle: "Hội thoại mới",
    },
    chatView: {
      conversationFallback: "Hội thoại",
      workspaceRuntime: "Runtime workspace",
      emptyTitle: "Hỏi đáp có công cụ, trích dẫn và ngữ cảnh đồ thị",
      emptyDescription:
        "Bắt đầu bằng câu hỏi trực tiếp. Mở phần Nâng cao khi cần giới hạn tài liệu, tinh chỉnh retrieval hoặc tạm bật/tắt công cụ.",
      streamingFailed: "Streaming thất bại",
      sendFailedPrefix: "Gửi thất bại:",
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
        "Quản lý thông tin xác thực provider và trạng thái sẵn sàng trong một màn hình.",
    },
    settingsShell: {
      general: {
        label: "Chung",
        description: "Workspace, ngôn ngữ, giao diện",
      },
      providers: {
        label: "Nhà cung cấp",
        description: "Cấu hình truy cập và trạng thái sẵn sàng của provider.",
      },
      models: {
        label: "Mô hình",
        description: "Danh mục model từ backend",
      },
    },
    generalSettings: {
      workspace: {
        title: "Workspace",
        description: "Workspace hiện đang hoạt động cho phiên này.",
        nameLabel: "Tên workspace",
        readyProvidersLabel: "Providers sẵn sàng",
        readyProvidersDescription: "Các provider LLM hiện đang báo trạng thái sẵn sàng.",
      },
      appearance: {
        title: "Giao diện",
        description: "Chọn ngôn ngữ và chủ đề màu.",
        languageLabel: "Ngôn ngữ",
        languageDescription: "Đổi ngôn ngữ hiển thị cho toàn bộ ứng dụng.",
        themeLabel: "Chủ đề",
        themeLoading: "Đang tải...",
        themeAppliedPrefix: "Đang áp dụng:",
        themeOptions: {
          light: "Sáng",
          dark: "Tối",
          system: "Hệ thống",
        },
      },
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
    chatRuntimeControls: {
      noProfile: "Không dùng hồ sơ",
      selectProfile: "Chọn hồ sơ",
      searchProviderModel: "Tìm provider hoặc model",
      selectModel: "Chọn model",
      sessionOverride: "Ghi đè theo phiên",
      profileManaged: "Theo cấu hình hồ sơ",
      agentPrefix: "Agent",
      profileLocksOverride: "Hồ sơ khóa quyền ghi đè model",
    },
    pages: {
      agents: {
        title: "Agents",
        description:
          "Quản lý hồ sơ agent, preset năng lực, chính sách công cụ, knowledge pack và phạm vi bằng chứng.",
      },
      artifacts: {
        title: "Artifacts",
        description:
          "Giao diện tạo artifact đang được dựng và chờ hợp đồng backend.",
      },
      ask: {
        newConversationHeading: "Bắt đầu cuộc hội thoại mới",
        description:
          "Chọn hồ sơ agent và tạo chat. Định tuyến model sẽ đến từ hồ sơ đó hoặc mặc định workspace.",
        workspaceDefault: "Mặc định workspace",
        newConversationButton: "Cuộc hội thoại mới",
        createFailedPrefix: "Tạo thất bại:",
        newConversationTitle: "Cuộc hội thoại mới",
      },
      connectors: {
        title: "Connectors",
        description: "Bảng điều khiển connector đang được dựng và chờ API.",
      },
      documents: {
        title: "Tài liệu",
        description:
          "Tải file để nạp. Các đoạn đã lập chỉ mục dùng cho truy xuất và trích xuất ontology.",
      },
      error: {
        title: "Đã xảy ra lỗi",
        tryAgain: "Thử lại",
        unexpectedMessage: "Lỗi ứng dụng không mong đợi.",
      },
      ontologyHub: {
        title: "Pipeline ontology",
        description:
          "Từ tài liệu đã lập chỉ mục đến ứng viên đã trích xuất, duyệt và phiên bản đồ thị đã xuất bản.",
        openGraphEditor: "Mở trình sửa đồ thị",
        recentBuilds: "Build gần đây",
      },
      ontologyBuilds: {
        title: "Các build ontology",
        description:
          "Mỗi build trích xuất thực thể và quan hệ ứng viên từ một tài liệu. Duyệt và xuất bản để đưa vào đồ thị.",
      },
      ontologyReview: {
        title: "Hàng đợi duyệt",
        description: "Tất cả ứng viên đang chờ trên các build trong workspace này.",
      },
      tasks: {
        title: "Tác vụ",
        description: "Xử lý tác vụ ad-hoc qua endpoint runtime công khai.",
      },
      tools: {
        title: "Công cụ Admin / Debug",
        description:
          "Chẩn đoán nội bộ cho registry công cụ và gọi trực tiếp. Route này không còn là luồng sản phẩm chính.",
      },
      workflows: {
        title: "Workflows",
        description: "Xem các workflow đã đăng ký và chạy các mục được hỗ trợ.",
      },
    },
    commandPalette: {
      inputPlaceholder: "Gõ lệnh hoặc tìm kiếm...",
      noResults: "Không có kết quả.",
      navigationHeading: "Điều hướng",
    },
    graph: {
      title: "Workbench đồ thị",
      subtitle: "Ontology đã xuất bản, kiểu schema và quan hệ có bằng chứng.",
      modeGraphOnly: "Chỉ đồ thị",
      modeSplit: "Chia màn hình",
      modeInspector: "Inspector",
      refresh: "Làm mới",
      versionBadge: "Phiên bản",
      entitiesBadge: "thực thể",
      relationsBadge: "quan hệ",
      publishedPrefix: "Xuất bản",
      noPublishedGraph: "Chưa có đồ thị đã xuất bản",
      searchNodesPlaceholder: "Tìm nút",
      filterTypesHint: "Loại thực thể",
      clearFilters: "Xóa lọc",
      allTypes: "Mọi loại",
      canvasTitle: "Canvas",
      loadFailedPrefix: "Không tải được đồ thị:",
      emptyState:
        "Chưa có phiên bản ontology đã xuất bản. Duyệt build, xuất bản, rồi mở lại đồ thị.",
      emptyCta: "Mở danh sách build ontology",
      legendTitle: "Chú giải",
      noEntityTypes: "Chưa có loại thực thể.",
      inspectorTitle: "Inspector",
      inspectorEmpty: "Chọn nút hoặc quan hệ để xem bằng chứng, alias và ngữ cảnh.",
      aliasesLabel: "Alias",
      noAliases: "Không có alias",
      sourceDocumentLabel: "Tài liệu nguồn",
      connectedEdges: "Kết nối",
      outgoing: "Đi ra",
      incoming: "Đi vào",
      selectNode: "Tập trung trên đồ thị",
      relationSource: "Nguồn",
      relationTarget: "Đích",
      confidenceLabel: "Độ tin cậy",
      evidenceLabel: "Bằng chứng",
      noEvidence: "Không có đoạn bằng chứng",
      zoomIn: "Phóng to",
      zoomOut: "Thu nhỏ",
      fitView: "Vừa khung",
      graphitiIndexed: "Đã index Graphiti",
    },
    agentManagement: {
      title: "Quản lý Agent",
      description:
        "Quản lý hồ sơ, preset năng lực, chính sách công cụ, knowledge pack và phạm vi bằng chứng.",
      profilesTitle: "Hồ sơ",
      profilesDescription: "Tạo hồ sơ tại đây. Thông tin provider nằm trong `/settings`.",
      newProfilePlaceholder: "Tên hồ sơ mới",
      create: "Tạo",
      noProfiles:
        "Chưa có hồ sơ. Tạo một hồ sơ để định preset, chính sách công cụ và phạm vi tri thức.",
      selectProfileHint: "Chọn hồ sơ để chỉnh danh tính, năng lực, knowledge và chính sách bằng chứng.",
      defaultBadge: "Mặc định",
      noDescription: "Không có mô tả",
      identityTitle: "Danh tính",
      identityDescription: "Prompt và hợp đồng hành vi cốt lõi của agent.",
      name: "Tên",
      status: "Trạng thái",
      descriptionLabel: "Mô tả",
      descriptionPlaceholder: "Agent này dùng để làm gì",
      systemPromptLabel: "System prompt",
      systemPromptPlaceholder: "Bạn là một agent phân tích...",
      capabilityTitle: "Năng lực",
      capabilityDescription: "Chọn preset trước, rồi thu hẹp công cụ trong phạm vi preset.",
      capabilityPreset: "Preset năng lực",
      selectPresetPlaceholder: "Chọn preset",
      toolPolicyMode: "Chế độ chính sách công cụ",
      policyPreset: "Preset",
      policyAllowlist: "Allowlist",
      policyBlocklist: "Blocklist",
      presetSummary: "Tóm tắt preset",
      noPresetSelected: "Chưa chọn preset",
      lanePalette: "Palette công cụ",
      lanePaletteHint: "Kéo công cụ vào Allowed hoặc Blocked. Tìm kiếm và mức rủi ro lọc danh sách.",
      laneAllowed: "Công cụ được phép",
      laneAllowedHint: "Thứ tự thể hiện ưu tiên; kéo để sắp xếp.",
      laneBlocked: "Công cụ bị chặn",
      laneBlockedHint: "Các công cụ này sẽ không chạy cho hồ sơ này (khi chính sách áp dụng).",
      searchToolsPlaceholder: "Tìm công cụ…",
      riskFilter: "Rủi ro",
      riskAll: "Tất cả",
      riskLow: "Thấp",
      riskMedium: "Trung bình",
      riskHigh: "Cao",
      removeFromLane: "Gỡ",
      noCatalogTools: "Chưa có mục catalog nào khớp preset này.",
      knowledgeTitle: "Phạm vi tri thức",
      knowledgeDescription: "Chọn pack cho hồ sơ và tạo/sửa pack tại chỗ.",
      newPack: "Pack mới",
      editKnowledgePack: "Sửa knowledge pack",
      createKnowledgePack: "Tạo knowledge pack",
      knowledgeDialogDescription: "Knowledge pack nằm trong luồng `/agents`.",
      cancel: "Hủy",
      savePack: "Lưu knowledge pack",
      packName: "Tên",
      packStatus: "Trạng thái",
      packDescription: "Mô tả",
      packDocuments: "Tài liệu",
      activeStatus: "Hoạt động",
      archivedStatus: "Lưu trữ",
      attachProfile: "Gắn vào hồ sơ này",
      linkedDocs: "tài liệu liên kết",
      noPacks: "Chưa có knowledge pack. Tạo pack và gắn tài liệu trước khi gán cho hồ sơ.",
      edit: "Sửa",
      evidenceTitle: "Chính sách bằng chứng",
      evidenceDescription: "Kiểm soát nguồn bằng chứng mà hồ sơ được dùng.",
      modelOnlyFallback: "Cho phép chỉ dùng model khi chính sách cho phép",
      editingSummary: "Đang sửa {name} với {preset} và {scope}.",
      setDefault: "Đặt mặc định",
      saveProfile: "Lưu hồ sơ",
      toastKnowledgePackSaved: "Đã lưu knowledge pack.",
      toastKnowledgePackSaveFailedPrefix: "Lưu knowledge pack thất bại:",
    },
    ontologyBuild: {
      notFound: "Không tìm thấy build.",
      back: "Quay lại",
      documentLabel: "Tài liệu",
      tabEntities: "Thực thể",
      tabRelations: "Quan hệ",
      tabSteps: "Bước",
      statEntities: "Thực thể",
      statPendingEntities: "Thực thể chờ",
      statRelations: "Quan hệ",
      statPendingRelations: "Quan hệ chờ",
      statExtractionModel: "Model trích xuất",
      stepColumnName: "Bước",
      stepColumnStatus: "Trạng thái",
      stepColumnDetail: "Chi tiết",
      stepColumnStarted: "Bắt đầu",
      stepColumnFinished: "Kết thúc",
      stepColumnDuration: "Thời lượng",
      noSteps: "Chưa có bước nào được ghi.",
      stepsProgress: "{done}/{total} bước đã hoàn thành",
      tableBuild: "Build",
      tableStatus: "Trạng thái",
      tableDomain: "Miền",
      tableModel: "Model",
      tableEntities: "Thực thể",
      tableRelations: "Quan hệ",
      tablePending: "Chờ",
      tableUpdated: "Cập nhật",
      statusFilterPlaceholder: "trạng thái hoặc all",
      emptyBuildsList: "Chưa có build ontology nào.",
    },
    ontologyUi: {
      unknownError: "Lỗi không xác định",
      failedToLoadBuilds: "Không thể tải danh sách build.",
      modelNotRecorded: "không có thông tin model",
      unknownProvider: "không rõ",
      unknownModel: "không rõ",
      filterDocuments: "Lọc tài liệu",
      pickDocument: "Chọn tài liệu",
      pickExtractionModel: "Chọn model trích xuất",
      queueing: "Đang xếp hàng...",
      startBuild: "Bắt đầu build",
      buildQueued: "Đã xếp hàng build ontology",
      buildFailedPrefix: "Build thất bại:",
      newBuild: "Build mới",
      runOntologyExtraction: "Chạy trích xuất ontology",
      runOntologyExtractionDescription:
        "Chọn tài liệu đã lập chỉ mục và model trích xuất, rồi đưa build vào hàng đợi để duyệt.",
      indexedDocument: "Tài liệu đã lập chỉ mục",
      extractionModel: "Model trích xuất",
      noIndexedDocumentsMatch: "Không có tài liệu đã lập chỉ mục nào khớp bộ lọc.",
    },
    toolsUi: {
      searchPlaceholder: "Tìm công cụ, họ công cụ hoặc capability",
      emptyState: "Không có công cụ nào khớp bộ lọc hiện tại.",
      loadFailedPrefix: "Không thể tải công cụ:",
      table: {
        tool: "Công cụ",
        family: "Họ",
        risk: "Rủi ro",
        runtimeTraits: "Đặc tính runtime",
        capabilities: "Capabilities",
        action: "Hành động",
      },
      runtime: {
        streaming: "Streaming",
        buffered: "Buffered",
        timeoutSuffix: "giây timeout",
        none: "không có",
      },
      filters: {
        all: "all",
      },
    },
    toolInvoke: {
      invoke: "Gọi",
      dialogTitleFallback: "Gọi công cụ",
      workspaceId: "Workspace ID",
      workspacePlaceholder: "workspace",
      workspaceRequired: "Workspace là bắt buộc.",
      taskType: "Loại tác vụ",
      argumentsJson: "Đối số (JSON)",
      schemaPrefix: "schema:",
      requiredPrefix: "bắt buộc:",
      parseErrorPrefix: "Lỗi parse JSON:",
      close: "Đóng",
      invoking: "Đang gọi...",
      invokeTool: "Gọi công cụ",
      invokeFailedPrefix: "Gọi thất bại:",
      successToast: "{tool} thành công - {evidence} bằng chứng, {latency}ms",
      partialToast: "{tool} một phần - gợi ý: {hints}",
      failedToast: "{tool} thất bại - {code}: {message}",
      hintsPrefix: "gợi ý:",
      tracePrefix: "trace",
      evidenceSummary: "{evidence} bằng chứng",
      artifactsLabel: "artifacts",
      evidenceLabel: "bằng chứng",
      unknownError: "không rõ",
      none: "không có",
      argumentsMustBeObject: "arguments phải là JSON object",
    },
    tasksUi: {
      runTask: "Chạy tác vụ",
      content: "Nội dung",
      contentPlaceholder: "Mô tả tác vụ cần xử lý",
      providerOptional: "Provider (tùy chọn)",
      modelOptional: "Model (tùy chọn)",
      resolving: "Đang xử lý...",
      resolveTask: "Xử lý tác vụ",
      result: "Kết quả",
      outputPrefix: "đầu ra",
      taskResolved: "Đã xử lý tác vụ.",
      taskFailedPrefix: "Tác vụ thất bại:",
    },
    citationsDrawer: {
      title: "Trích dẫn",
      description: "Các đoạn bằng chứng được dùng để tạo câu trả lời.",
      citationCount: "{count} trích dẫn{suffix}",
    },
    evidenceUi: {
      title: "Bằng chứng",
      description: "Tìm kiếm trích dẫn retrieval và provenance của ontology cạnh nhau.",
      searchPlaceholder: "Tìm các chunk đã lập chỉ mục...",
      sourcesLabel: "Nguồn",
      includeOntology: "Bao gồm ứng viên ontology (build mới nhất)",
      promoteComingSoon: "promote: sắp có",
      emptyState: "Chạy tìm kiếm hoặc bật ứng viên ontology để đổ dữ liệu bằng chứng.",
      previous: "Trước",
      next: "Sau",
      retrievalSource: "Retrieval",
      documentSource: "Tài liệu",
      ontologyEntitySource: "Thực thể ontology",
      ontologyRelationSource: "Quan hệ ontology",
      searchFailedPrefix: "Tìm kiếm thất bại:",
    },
    evidenceDetail: {
      retrievalCitation: "Trích dẫn retrieval",
      documentChunk: "Chunk tài liệu",
      ontologyCandidateEntity: "Ứng viên thực thể ontology",
      ontologyCandidateRelation: "Ứng viên quan hệ ontology",
      scorePrefix: "điểm",
      trustPrefix: "tin cậy",
      snippet: "Đoạn trích",
      provenance: "Nguồn gốc",
      links: "Liên kết",
      openDocument: "Mở tài liệu",
      openBuild: "Mở build",
      externalSource: "Nguồn ngoài",
    },
  },
};
