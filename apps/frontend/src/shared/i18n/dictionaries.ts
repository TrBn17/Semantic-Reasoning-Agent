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
    knowledgePacks: string;
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
    renameWorkspace: string;
    deleteWorkspace: string;
    createTitle: string;
    createDescription: string;
    renameTitle: string;
    renameDescription: string;
    workspaceIdLabel: string;
    workspaceIdPlaceholder: string;
    workspaceIdHint: string;
    workspaceNameLabel: string;
    workspaceNamePlaceholder: string;
    deleteConfirm: string;
    createAndSwitch: string;
    toasts: {
      idRequired: string;
      nameRequired: string;
      selectWorkspace: string;
      switchedTo: string;
      workspaceUpdated: string;
      workspaceDeleted: string;
    };
  };
  documents: {
    uploadTitle: string;
    uploadDescription: string;
    fileLabel: string;
    ingestionModeLabel: string;
    ingestionModeOntology: string;
    ingestionModeRetrieval: string;
    ingestionModeBoth: string;
    ingestionModeHint: string;
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
      workspaceRequired: string;
      knowledgePackNameRequired: string;
      knowledgePackRequired: string;
      documentAddedToKnowledge: string;
      outOfScopeDocument: string;
    };
    knowledgePack: {
      label: string;
      selectPlaceholder: string;
      createNew: string;
      newNamePlaceholder: string;
      documentSelectLabel: string;
      documentSelectPlaceholder: string;
      addButton: string;
    };
  };
  knowledgePacksPage: {
    title: string;
    createTitle: string;
    namePlaceholder: string;
    createButton: string;
    tableDocument: string;
    tableChunks: string;
    emptyState: string;
    emptySelectedPack: string;
    documentsHint: string;
    toasts: {
      workspaceRequired: string;
      emptyName: string;
      selectPackToDelete: string;
      created: string;
      deleted: string;
    };
  };
  searchToolsPage: {
    title: string;
    description: string;
    tabs: {
      docs: string;
      graph: string;
    };
    docsHint: string;
    graphHint: string;
    loadFailedPrefix: string;
    emptyStatePrefix: string;
    emptyStateDocs: string;
    emptyStateGraph: string;
    emptyStateSuffix: string;
    newTool: string;
    newPrefix: string;
    searchToolSuffix: string;
    system: string;
    ready: string;
    blocked: string;
    duplicateToolAria: string;
    deleteToolAria: string;
    deleteConfirm: string;
    queryPlaceholder: string;
    run: string;
    hits: string;
    hintsPrefix: string;
    scorePrefix: string;
    nameLabel: string;
    namePlaceholder: string;
    descriptionLabel: string;
    descriptionHint: string;
    legacyProviderModel: string;
    legacyProviderModelHint: string;
    embeddingProvider: string;
    embeddingProviderHint: string;
    embeddingModel: string;
    embeddingModelHint: string;
    defaultTopK: string;
    collectionTarget: string;
    collectionWorkspace: string;
    collectionDocuments: string;
    documentsLabel: string;
    documentsHint: string;
    noDocuments: string;
    bm25Hint: string;
    enableBm25: string;
    fusionStrategy: string;
    semanticOnly: string;
    bm25Only: string;
    hybridRrf: string;
    ontologyScope: string;
    ontologyPublished: string;
    ontologyVersion: string;
    ontologyVersionId: string;
    ontologyVersionHint: string;
    graphSearchType: string;
    graphCombined: string;
    graphNodes: string;
    graphEdges: string;
    reranker: string;
    rerankerRrf: string;
    rerankerCrossEncoder: string;
    rerankerNone: string;
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
    workflows: { title: string; description: string; comingSoonBadge: string; comingSoonDetail: string };
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
    deleted: string;
    deleteFailed: string;
    deleteConfirm: string;
    publish: string;
    publishing: string;
    publishSuccess: string;
    publishFailed: string;
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
      knowledgePacks: "Knowledge",
      settings: "Settings",
    },
    home: {
      title: "Workspace",
      subtitle: "Knowledge operations cockpit for ask, documents, evidence, ontology, and graph.",
      quickActions: {
        ask: {
          title: "Ask a question",
          description: "",
        },
        documents: {
          title: "Upload document",
          description: "",
        },
        evidence: {
          title: "Browse evidence",
          description: "",
        },
        ontology: {
          title: "Review ontology builds",
          description: "",
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
      renameWorkspace: "Rename workspace",
      deleteWorkspace: "Delete workspace",
      createTitle: "Create Workspace",
      createDescription: "Create a new workspace.",
      renameTitle: "Rename Workspace",
      renameDescription: "Update workspace display name.",
      workspaceIdLabel: "Workspace ID (slug)",
      workspaceIdPlaceholder: "e.g. project-x, financial-analysis",
      workspaceIdHint: "Lowercase, no spaces. This will be used in Neo4j and SQL.",
      workspaceNameLabel: "Workspace name",
      workspaceNamePlaceholder: "e.g. Product Team",
      deleteConfirm: "Delete workspace \"{name}\"?",
      createAndSwitch: "Create & Switch",
      toasts: {
        idRequired: "Workspace ID is required",
        nameRequired: "Workspace name is required",
        selectWorkspace: "Please select a workspace.",
        switchedTo: "Switched to workspace:",
        workspaceUpdated: "Workspace updated: {name}",
        workspaceDeleted: "Workspace deleted: {name}",
      },
    },
    documents: {
      uploadTitle: "Upload a document",
      uploadDescription: "PDF, DOCX, XLSX, or CSV. Parsed and indexed by the ingestion worker.",
      fileLabel: "File",
      ingestionModeLabel: "Ingestion mode",
      ingestionModeOntology: "Ontology only",
      ingestionModeRetrieval: "Retrieval only",
      ingestionModeBoth: "Both",
      ingestionModeHint: "Choose whether to run ontology, retrieval indexing, or both in parallel.",
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
        workspaceRequired: "Workspace is not ready yet. Please select a workspace first.",
        knowledgePackNameRequired: "Please enter a knowledge collection name.",
        knowledgePackRequired: "Please select a knowledge collection.",
        documentAddedToKnowledge: "Document added to Knowledge.",
        outOfScopeDocument: "The selected document does not belong to this workspace or knowledge pack.",
      },
      knowledgePack: {
        label: "Knowledge",
        selectPlaceholder: "Select Knowledge",
        createNew: "+ Create new Knowledge",
        newNamePlaceholder: "Enter a new Knowledge name",
        documentSelectLabel: "Document",
        documentSelectPlaceholder: "Select document",
        addButton: "Add to Knowledge",
      },
    },
    knowledgePacksPage: {
      title: "Knowledge",
      createTitle: "Create Knowledge",
      namePlaceholder: "Knowledge name",
      createButton: "Create",
      tableDocument: "Document",
      tableChunks: "Chunks",
      emptyState: "No Knowledge yet.",
      emptySelectedPack: "No documents in the selected collection.",
      documentsHint: "Add documents from the Documents tab.",
      toasts: {
        workspaceRequired: "Workspace is not ready yet. Please select a workspace first.",
        emptyName: "Knowledge name cannot be empty.",
        selectPackToDelete: "Please select a Knowledge to delete.",
        created: "Knowledge created.",
        deleted: "Knowledge deleted.",
      },
    },
    searchToolsPage: {
      title: "Search Tools",
      description:
        "Create reusable super-search tools over documents or the ontology graph. Pick provider + model once, then invoke with a single click.",
      tabs: {
        docs: "Document Search",
        graph: "Graph Search",
      },
      docsHint:
        "Semantic + optional BM25 retrieval across a Qdrant collection or selected documents.",
      graphHint:
        "Ontology graph search - published snapshot or a specific version, with configurable reranker.",
      loadFailedPrefix: "Failed to load configurations:",
      emptyStatePrefix: "No saved",
      emptyStateDocs: "document",
      emptyStateGraph: "graph",
      emptyStateSuffix: "search tools yet. Click",
      newTool: "New tool",
      newPrefix: "New",
      searchToolSuffix: "search tool",
      system: "system",
      ready: "ready",
      blocked: "blocked",
      duplicateToolAria: "Duplicate tool",
      deleteToolAria: "Delete tool",
      deleteConfirm: "Delete \"{name}\"?",
      queryPlaceholder: "Type a query and press Run...",
      run: "Run",
      hits: "{count} hits",
      hintsPrefix: "Hints:",
      scorePrefix: "score",
      nameLabel: "Name",
      namePlaceholder: "e.g. Delivery ops retrieval",
      descriptionLabel: "Description",
      descriptionHint: "Shown on the tool card.",
      legacyProviderModel: "Legacy provider + model",
      legacyProviderModelHint:
        "Optional compatibility fields. If omitted, workspace embedding defaults are used.",
      embeddingProvider: "Embedding provider",
      embeddingProviderHint: "Defaults to the workspace search embedding provider.",
      embeddingModel: "Embedding model",
      embeddingModelHint: "Defaults to the workspace search embedding model.",
      defaultTopK: "Default top_k",
      collectionTarget: "Collection target",
      collectionWorkspace: "Whole workspace",
      collectionDocuments: "Selected documents",
      documentsLabel: "Documents",
      documentsHint: "Pick one or more indexed documents to scope this tool.",
      noDocuments: "No documents yet.",
      bm25Hint: "Toggle keyword scoring alongside semantic search.",
      enableBm25: "Enable BM25",
      fusionStrategy: "Fusion strategy",
      semanticOnly: "Semantic only",
      bm25Only: "BM25 only",
      hybridRrf: "Hybrid (Semantic + BM25, RRF)",
      ontologyScope: "Ontology scope",
      ontologyPublished: "Published snapshot (default)",
      ontologyVersion: "Specific version",
      ontologyVersionId: "Ontology version id",
      ontologyVersionHint: "Paste the ontology_version_id to target.",
      graphSearchType: "Graph search type",
      graphCombined: "Combined (nodes + edges)",
      graphNodes: "Nodes",
      graphEdges: "Edges",
      reranker: "Reranker",
      rerankerRrf: "RRF (light, no extra model)",
      rerankerCrossEncoder: "Cross-encoder",
      rerankerNone: "None",
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
      description: "",
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
      description: "",
    },
    settingsShell: {
      general: {
        label: "General",
        description: "",
      },
      providers: {
        label: "Providers",
        description: "",
      },
      models: {
        label: "Models",
        description: "",
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
        description: "",
      },
      artifacts: {
        title: "Artifacts",
        description: "",
      },
      ask: {
        newConversationHeading: "Start a new conversation",
        description: "",
        workspaceDefault: "Workspace default",
        newConversationButton: "New conversation",
        createFailedPrefix: "Failed to create:",
        newConversationTitle: "New conversation",
      },
      connectors: {
        title: "Connectors",
        description: "",
      },
      documents: {
        title: "Documents",
        description: "",
      },
      error: {
        title: "Something went wrong",
        tryAgain: "Try again",
        unexpectedMessage: "Unexpected application error.",
      },
      ontologyHub: {
        title: "Ontology pipeline",
        description: "",
        openGraphEditor: "Open Graph Editor",
        recentBuilds: "Recent builds",
      },
      ontologyBuilds: {
        title: "Ontology builds",
        description: "",
      },
      ontologyReview: {
        title: "Review queue",
        description: "",
      },
      tasks: {
        title: "Tasks",
        description: "",
      },
      tools: {
        title: "Admin / Debug Tools",
        description: "",
      },
      workflows: {
        title: "Workflows",
        description: "",
        comingSoonBadge: "Coming soon",
        comingSoonDetail: "",
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
      description: "",
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
      deleted: "Ontology deleted.",
      deleteFailed: "Failed to delete ontology.",
      deleteConfirm: "Delete ontology {id}?",
      publish: "Publish",
      publishing: "Publishing...",
      publishSuccess: "Published to graph.",
      publishFailed: "Failed to publish ontology.",
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
      description: "",
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
      knowledgePacks: "Knowledge",
      settings: "Cài đặt",
    },
    home: {
      title: "Không gian làm việc",
      subtitle: "Bảng điều khiển cho hỏi đáp, tài liệu, bằng chứng, ontology và đồ thị.",
      quickActions: {
        ask: {
          title: "Đặt câu hỏi",
          description: "",
        },
        documents: {
          title: "Tải tài liệu lên",
          description: "",
        },
        evidence: {
          title: "Duyệt bằng chứng",
          description: "",
        },
        ontology: {
          title: "Duyệt build ontology",
          description: "",
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
      renameWorkspace: "Đổi tên workspace",
      deleteWorkspace: "Xóa workspace",
      createTitle: "Tạo Workspace",
      createDescription: "Tạo workspace mới.",
      renameTitle: "Đổi tên Workspace",
      renameDescription: "Cập nhật tên hiển thị cho workspace.",
      workspaceIdLabel: "Workspace ID (slug)",
      workspaceIdPlaceholder: "ví dụ: project-x, phan-tich-tai-chinh",
      workspaceIdHint: "Viết thường, không dấu, không khoảng cách. Dùng cho Neo4j và SQL.",
      workspaceNameLabel: "Tên workspace",
      workspaceNamePlaceholder: "ví dụ: Đội sản phẩm",
      deleteConfirm: "Xóa workspace \"{name}\"?",
      createAndSwitch: "Tạo & Chuyển",
      toasts: {
        idRequired: "Yêu cầu nhập Workspace ID",
        nameRequired: "Yêu cầu nhập tên workspace",
        selectWorkspace: "Vui lòng chọn workspace.",
        switchedTo: "Đã chuyển sang workspace:",
        workspaceUpdated: "Đã cập nhật workspace: {name}",
        workspaceDeleted: "Đã xóa workspace: {name}",
      },
    },
    documents: {
      uploadTitle: "Tải tài liệu lên",
      uploadDescription: "Hỗ trợ PDF, DOCX, XLSX, hoặc CSV. Tài liệu sẽ được xử lý bởi worker.",
      fileLabel: "Tệp tin",
      ingestionModeLabel: "Chế độ ingest",
      ingestionModeOntology: "Chỉ ontology",
      ingestionModeRetrieval: "Chỉ retrieval",
      ingestionModeBoth: "Cả hai",
      ingestionModeHint: "Chọn chạy ontology, lập chỉ mục retrieval, hoặc chạy song song cả hai.",
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
        workspaceRequired: "Workspace chưa sẵn sàng. Vui lòng chọn workspace trước.",
        knowledgePackNameRequired: "Vui lòng nhập tên bộ tri thức mới.",
        knowledgePackRequired: "Vui lòng chọn bộ tri thức.",
        documentAddedToKnowledge: "Đã thêm tài liệu vào Knowledge.",
        outOfScopeDocument: "Tài liệu đã chọn không thuộc workspace hoặc bộ tri thức hiện tại.",
      },
      knowledgePack: {
        label: "Knowledge",
        selectPlaceholder: "Chọn Knowledge",
        createNew: "+ Tạo Knowledge mới",
        newNamePlaceholder: "Nhập tên Knowledge mới",
        documentSelectLabel: "Tài liệu",
        documentSelectPlaceholder: "Chọn tài liệu",
        addButton: "Thêm vào Knowledge",
      },
    },
    knowledgePacksPage: {
      title: "Knowledge",
      createTitle: "Tạo Knowledge",
      namePlaceholder: "Tên Knowledge",
      createButton: "Tạo",
      tableDocument: "Tài liệu",
      tableChunks: "Chunks",
      emptyState: "Chưa có Knowledge nào.",
      emptySelectedPack: "Chưa có tài liệu trong bộ tri thức được chọn.",
      documentsHint: "Thêm tài liệu ở tab Documents.",
      toasts: {
        workspaceRequired: "Workspace chưa sẵn sàng. Vui lòng chọn workspace trước.",
        emptyName: "Tên Knowledge không được để trống.",
        selectPackToDelete: "Hãy chọn Knowledge cần xóa.",
        created: "Đã tạo Knowledge.",
        deleted: "Đã xóa Knowledge.",
      },
    },
    searchToolsPage: {
      title: "Công cụ tìm kiếm",
      description:
        "Tạo công cụ super-search dùng lại trên tài liệu hoặc đồ thị ontology. Chọn provider + model một lần rồi gọi chỉ với một lần bấm.",
      tabs: {
        docs: "Tìm kiếm tài liệu",
        graph: "Tìm kiếm đồ thị",
      },
      docsHint:
        "Truy xuất semantic + BM25 (tùy chọn) trên collection Qdrant hoặc tập tài liệu được chọn.",
      graphHint:
        "Tìm kiếm đồ thị ontology - snapshot đã xuất bản hoặc phiên bản cụ thể, với reranker có thể cấu hình.",
      loadFailedPrefix: "Không thể tải cấu hình:",
      emptyStatePrefix: "Chưa có công cụ tìm kiếm",
      emptyStateDocs: "tài liệu",
      emptyStateGraph: "đồ thị",
      emptyStateSuffix: ". Nhấn",
      newTool: "Công cụ mới",
      newPrefix: "Tạo",
      searchToolSuffix: "search tool",
      system: "hệ thống",
      ready: "sẵn sàng",
      blocked: "bị chặn",
      duplicateToolAria: "Nhân bản công cụ",
      deleteToolAria: "Xóa công cụ",
      deleteConfirm: "Xóa \"{name}\"?",
      queryPlaceholder: "Nhập truy vấn và nhấn Chạy...",
      run: "Chạy",
      hits: "{count} kết quả",
      hintsPrefix: "Gợi ý:",
      scorePrefix: "điểm",
      nameLabel: "Tên",
      namePlaceholder: "ví dụ: truy xuất vận hành giao hàng",
      descriptionLabel: "Mô tả",
      descriptionHint: "Hiển thị trên thẻ công cụ.",
      legacyProviderModel: "Provider + model cũ",
      legacyProviderModelHint:
        "Trường tương thích tùy chọn. Nếu bỏ trống, hệ thống dùng mặc định embedding của workspace.",
      embeddingProvider: "Provider embedding",
      embeddingProviderHint: "Mặc định theo provider embedding của workspace.",
      embeddingModel: "Model embedding",
      embeddingModelHint: "Mặc định theo model embedding của workspace.",
      defaultTopK: "top_k mặc định",
      collectionTarget: "Phạm vi collection",
      collectionWorkspace: "Toàn workspace",
      collectionDocuments: "Tài liệu được chọn",
      documentsLabel: "Tài liệu",
      documentsHint: "Chọn một hoặc nhiều tài liệu đã lập chỉ mục để giới hạn công cụ này.",
      noDocuments: "Chưa có tài liệu.",
      bm25Hint: "Bật/tắt điểm keyword song song với semantic search.",
      enableBm25: "Bật BM25",
      fusionStrategy: "Chiến lược trộn điểm",
      semanticOnly: "Chỉ semantic",
      bm25Only: "Chỉ BM25",
      hybridRrf: "Hybrid (Semantic + BM25, RRF)",
      ontologyScope: "Phạm vi ontology",
      ontologyPublished: "Snapshot đã xuất bản (mặc định)",
      ontologyVersion: "Phiên bản cụ thể",
      ontologyVersionId: "ID phiên bản ontology",
      ontologyVersionHint: "Dán ontology_version_id cần truy vấn.",
      graphSearchType: "Loại tìm kiếm đồ thị",
      graphCombined: "Kết hợp (nút + cạnh)",
      graphNodes: "Nút",
      graphEdges: "Cạnh",
      reranker: "Reranker",
      rerankerRrf: "RRF (nhẹ, không cần model phụ)",
      rerankerCrossEncoder: "Cross-encoder",
      rerankerNone: "Không dùng",
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
      description: "",
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
      description: "",
    },
    settingsShell: {
      general: {
        label: "Chung",
        description: "",
      },
      providers: {
        label: "Nhà cung cấp",
        description: "",
      },
      models: {
        label: "Mô hình",
        description: "",
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
        description: "",
      },
      artifacts: {
        title: "Artifacts",
        description: "",
      },
      ask: {
        newConversationHeading: "Bắt đầu cuộc hội thoại mới",
        description: "",
        workspaceDefault: "Mặc định workspace",
        newConversationButton: "Cuộc hội thoại mới",
        createFailedPrefix: "Tạo thất bại:",
        newConversationTitle: "Cuộc hội thoại mới",
      },
      connectors: {
        title: "Connectors",
        description: "",
      },
      documents: {
        title: "Tài liệu",
        description: "",
      },
      error: {
        title: "Đã xảy ra lỗi",
        tryAgain: "Thử lại",
        unexpectedMessage: "Lỗi ứng dụng không mong đợi.",
      },
      ontologyHub: {
        title: "Pipeline ontology",
        description: "",
        openGraphEditor: "Mở trình sửa đồ thị",
        recentBuilds: "Build gần đây",
      },
      ontologyBuilds: {
        title: "Các build ontology",
        description: "",
      },
      ontologyReview: {
        title: "Hàng đợi duyệt",
        description: "",
      },
      tasks: {
        title: "Tác vụ",
        description: "",
      },
      tools: {
        title: "Công cụ Admin / Debug",
        description: "",
      },
      workflows: {
        title: "Workflows",
        description: "",
        comingSoonBadge: "Sắp ra mắt",
        comingSoonDetail: "",
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
      deleted: "Đã xóa ontology.",
      deleteFailed: "Không thể xóa ontology.",
      deleteConfirm: "Xóa ontology {id}?",
      publish: "Publish",
      publishing: "Đang publish...",
      publishSuccess: "Đã publish vào graph.",
      publishFailed: "Không thể publish ontology.",
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
      description: "",
      citationCount: "{count} trích dẫn{suffix}",
    },
    evidenceUi: {
      title: "Bằng chứng",
      description: "",
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
