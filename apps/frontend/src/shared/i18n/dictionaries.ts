export type Language = "en" | "vi";

export type Dictionary = {
  appName: string;
  languageLabel: string;
  languageOptions: {
    english: string;
    vietnamese: string;
  };
  common: {
    loading: string;
    close: string;
    invoke: string;
    invoking: string;
    invokeFailed: string;
    cancel: string;
    upload: string;
    uploading: string;
    uploadSelected: string;
    uploaded: string;
    uploadFailedPrefix: string;
    uploadDescription: string;
    file: string;
    files: string;
    selected: string;
    tags: string;
    tagsPlaceholder: string;
    commaSeparated: string;
    selectAtLeastOneFile: string;
    failedToLoadDocuments: string;
    noDocumentsYet: string;
    title: string;
    type: string;
    status: string;
    chunks: string;
    updated: string;
    selectProfile: string;
    selectModel: string;
    workspaceDefault: string;
    modelUpdateFailedPrefix: string;
    profileUpdateFailedPrefix: string;
    sessionOverride: string;
    inheritedDefault: string;
    profileLocksModelOverride: string;
    none: string;
    unknown: string;
    schema: string;
    required: string;
    evidence: string;
    artifacts: string;
    hints: string;
    jsonParseError: string;
    workspaceId: string;
    taskType: string;
    na: string;
    workspaceRequired: string;
    serviceUnavailable: string;
  };
  layout: {
    brandTagline: string;
    controlPlaneLabel: string;
    logoAlt: string;
  };
  workspaceControlPlane: string;
  nav: {
    work: string;
    knowledge: string;
    automation: string;
    outputs: string;
    admin: string;
    home: string;
    agents: string;
    ask: string;
    documents: string;
    evidence: string;
    ontology: string;
    graph: string;
    tasks: string;
    workflows: string;
    tools: string;
    connectors: string;
    artifacts: string;
    settings: string;
  };
  home: {
    heroBadge: string;
    title: string;
    subtitle: string;
    summary: {
      documents: string;
      graphEntities: string;
      conversations: string;
    };
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
    languageTitle: string;
    languageDescription: string;
    agentProfilesTitle: string;
    agentProfilesDescription: string;
    openAgents: string;
  };
  agentsPage: {
    heroBadge: string;
    title: string;
    subtitle: string;
    readinessTitle: string;
    readinessDescription: string;
    readyToReview: string;
    needsSetup: string;
    profileName: string;
    systemPrompt: string;
    chatRouting: string;
    chatModelReady: string;
    catalogTitle: string;
    catalogDescription: string;
    new: string;
    newDraftTitle: string;
    newDraftDescription: string;
    draft: string;
    noDescription: string;
    default: string;
    builderDescription: string;
    makeDefault: string;
    saveAgent: string;
    tabIdentity: string;
    tabBehavior: string;
    tabRouting: string;
    tabPreview: string;
    agentName: string;
    agentNamePlaceholder: string;
    roleSummary: string;
    roleSummaryPlaceholder: string;
    allowOverride: string;
    promptPlaceholder: string;
    promptHint: string;
    previewTitle: string;
    previewDescription: string;
    settingsTitle: string;
    settingsDescription: string;
    settingsHint: string;
    openSettings: string;
    livePreviewTitle: string;
    livePreviewDescription: string;
    notAssigned: string;
    flexibleOverride: string;
    lockedOverride: string;
    testPrompt: string;
    retrievalEnabled: string;
    testAgent: string;
    lastResult: string;
    toolUsage: string;
    noToolUsage: string;
    openRunDetails: string;
    viewAllRuns: string;
    recentContextTitle: string;
    updated: string;
    unsavedDraft: string;
    runtimeCheckReady: string;
    needsWork: string;
  };
  askLanding: {
    newConversationTitle: string;
    newConversationBody: string;
    newConversationButton: string;
    defaultConversationTitle: string;
  };
  documentsPage: {
    title: string;
    description: string;
  };
  ontologyPage: {
    title: string;
    description: string;
    recentBuilds: string;
  };
  ontologyReviewPage: {
    title: string;
    description: string;
  };
  taskDetailPage: {
    backToTasks: string;
    title: string;
    runSummaryTitle: string;
    runSummaryDescription: string;
    metaTaskType: string;
    metaRequestedOutput: string;
    metaWorkflow: string;
    metaProvider: string;
    metaModel: string;
    metaUpdated: string;
    unassigned: string;
    na: string;
    outputSnapshotTitle: string;
    errorTitle: string;
    toolCallsTitle: string;
    toolCallsDescription: string;
    noToolCalls: string;
    colTool: string;
    colStatus: string;
    colTrace: string;
    colLatency: string;
    colStarted: string;
    taskNotFound: string;
    profileId: string;
  };
  /** Routes linked from nav before full feature UI exists */
  placeholderPages: {
    connectors: { title: string; description: string };
    artifacts: { title: string; description: string };
  };
  chat: {
    conversations: string;
    newChat: string;
    conversationCreated: string;
    conversationCreateFailedPrefix: string;
    loadConversationsFailed: string;
    noConversationsYet: string;
  };
  toolsPage: {
    heroBadge: string;
    title: string;
    subtitle: string;
  };
  tasksPage: {
    heroBadge: string;
    title: string;
    subtitle: string;
    completed: string;
    running: string;
    failed: string;
    taskRuns: string;
    taskRunsDescription: string;
    searchPlaceholder: string;
    filterStatus: string;
    statusAll: string;
    statusPending: string;
    statusRunning: string;
    statusCompleted: string;
    statusFailed: string;
    noMatches: string;
    tableTask: string;
    tableStatus: string;
    tableWorkflow: string;
    tableRuntime: string;
    tableUpdated: string;
    tableDetails: string;
    unassigned: string;
    openDetails: string;
  };
  workflowsPage: {
    heroBadge: string;
    title: string;
    subtitle: string;
    registrySnapshot: string;
    registered: string;
    runs: string;
    registryTitle: string;
    registryDescription: string;
    runCardTitle: string;
    runCardDescription: string;
    noWorkflowSelected: string;
    pickWorkflowFirst: string;
    prompt: string;
    provider: string;
    model: string;
    runButton: string;
    recentRuns: string;
    recentRunsDescription: string;
    noRunsForFilter: string;
    selectWorkflowFirstError: string;
    runSubmitted: string;
    runFailedPrefix: string;
    defaultPrompt: string;
    taskLabel: string;
  };
  /** Knowledge graph UI copy */
  knowledgeGraph: {
    buildsPage: { title: string; subtitle: string };
    buildTable: {
      loadFailed: string;
      cardTitle: string;
      cardDescription: string;
      metricEntities: string;
      metricRelations: string;
      metricVersion: string;
      footerBeforeLink: string;
      graphExplorerLink: string;
      footerAfterLink: string;
    };
    graphStats: {
      loadFailed: string;
      publishedEntities: string;
      publishedRelations: string;
      latestVersion: string;
      buildPrefix: string;
      entitiesSection: string;
      colName: string;
      colType: string;
      colAliases: string;
      colSourceDoc: string;
      emptyEntitiesRow: string;
    };
    buildDetail: {
      title: string;
      description: string;
      back: string;
    };
    crossReview: {
      intro: string;
      codePath: string;
      afterCode: string;
      extract: string;
      or: string;
      ingest: string;
      onThe: string;
      pageThen: string;
      end: string;
    };
    extractDialog: {
      trigger: string;
      title: string;
      description: string;
      documentsLabel: string;
      selected: string;
      unselected: string;
      noIndexedDocs: string;
      nSelected: string;
      cancel: string;
      run: string;
      running: string;
      pickError: string;
      toastPublished: string;
      toastPartial: string;
      toastFailed: string;
      toastError: string;
    };
    ingestDialog: {
      trigger: string;
      title: string;
      description: string;
      chooseFiles: string;
      uploading: string;
      close: string;
      toastSuccess: string;
      toastError: string;
    };
    documentCard: {
      title: string;
      link: string;
      body: string;
    };
  };
  evidencePage: {
    title: string;
    subtitle: string;
    searchPlaceholder: string;
    topKLabel: string;
    search: string;
    sourcesLabel: string;
    includeGraph: string;
    promoteBadge: string;
    empty: string;
    searchFailedPrefix: string;
    drawerSnippet: string;
    drawerProvenance: string;
    drawerLinks: string;
    scoreBadgePrefix: string;
    trustBadgePrefix: string;
    emptyPreview: string;
    sourceLabels: {
      retrieval: string;
      document: string;
      candidateEntity: string;
      candidateRelation: string;
      graphEntity: string;
      graphRelation: string;
    };
    drawerSourceLabels: {
      retrieval: string;
      document: string;
      candidateEntity: string;
      candidateRelation: string;
      graphEntity: string;
      graphRelation: string;
    };
    openDocument: string;
    openBuild: string;
    externalSource: string;
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
  tools: {
    title: string;
    table: {
      tool: string;
      family: string;
      risk: string;
      capabilities: string;
      timeout: string;
      action: string;
    };
    empty: string;
    loadFailedPrefix: string;
    risk: {
      low: string;
      medium: string;
      high: string;
    };
    invokeDialog: {
      title: string;
      workspaceId: string;
      taskType: string;
      arguments: string;
      close: string;
      invoke: string;
      invoking: string;
      schemaPrefix: string;
      requiredPrefix: string;
      parseErrorPrefix: string;
      argumentsObjectError: string;
      status: {
        success: string;
        partial: string;
        failed: string;
      };
      results: {
        summary: string;
        hints: string;
        evidence: string;
        artifacts: string;
        trace: string;
      };
      defaults: {
        workspacePlaceholder: string;
        taskType: string;
      };
    };
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
    common: {
      loading: "Loading...",
      close: "Close",
      invoke: "Invoke",
      invoking: "Invoking...",
      invokeFailed: "Invoke failed:",
      cancel: "Cancel",
      upload: "Upload",
      uploading: "Uploading...",
      uploadSelected: "Upload selected",
      uploaded: "Uploaded",
      uploadFailedPrefix: "Upload failed:",
      uploadDescription:
        "PDF, DOCX, or XLSX. Select multiple files and the ingestion worker will process them in batch.",
      file: "file",
      files: "files",
      selected: "Selected",
      tags: "Tags",
      tagsPlaceholder: "e.g. policy,2025",
      commaSeparated: "comma separated",
      selectAtLeastOneFile: "Select at least one file to upload",
      failedToLoadDocuments: "Failed to load documents.",
      noDocumentsYet: "No documents yet. Upload a PDF, DOCX, or XLSX to start.",
      title: "Title",
      type: "Type",
      status: "Status",
      chunks: "Chunks",
      updated: "Updated",
      selectProfile: "Select profile",
      selectModel: "Select model",
      workspaceDefault: "Workspace default",
      modelUpdateFailedPrefix: "Model update failed:",
      profileUpdateFailedPrefix: "Profile update failed:",
      sessionOverride: "Session override",
      inheritedDefault: "Inherited default",
      profileLocksModelOverride: "Profile locks model override",
      none: "none",
      unknown: "unknown",
      schema: "schema",
      required: "required",
      evidence: "evidence",
      artifacts: "artifacts",
      hints: "hints",
      jsonParseError: "JSON parse error",
      workspaceId: "Workspace ID",
      taskType: "Task type",
      na: "n/a",
      workspaceRequired: "Select a workspace before running this action.",
      serviceUnavailable: "Service unavailable",
    },
    layout: {
      brandTagline: "Semantic reasoning workspace",
      controlPlaneLabel: "Control plane",
      logoAlt: "Semantic Agent logo",
    },
    workspaceControlPlane: "Workspace control plane",
    nav: {
      work: "Work",
      knowledge: "Knowledge",
      automation: "Automation",
      outputs: "Outputs",
      admin: "Admin",
      home: "Home",
      agents: "Agents",
      ask: "Ask",
      documents: "Documents",
      evidence: "Evidence",
      ontology: "Ontology",
      graph: "Graph",
      tasks: "Tasks",
      workflows: "Workflows",
      tools: "Tools",
      connectors: "Connectors",
      artifacts: "Artifacts",
      settings: "Settings",
    },
    home: {
      heroBadge: "Knowledge operations cockpit",
      title: "Workspace",
      subtitle: "Knowledge operations cockpit for ask, documents, evidence, ontology, and graph.",
      summary: {
        documents: "Docs",
        graphEntities: "Graph entities",
        conversations: "Chats",
      },
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
          "Task runs, workflow catalog, and artifact generation will appear here as this workspace enables more automation surfaces.",
      },
    },
    settingsPage: {
      title: "Settings",
      description: "Application-level preferences live here.",
      languageTitle: "Language",
      languageDescription: "Choose the UI language for the workspace shell.",
      agentProfilesTitle: "Agent profiles moved",
      agentProfilesDescription:
        "Provider setup, default models, and agent profile management now live on the Agents page.",
      openAgents: "Open Agents",
    },
    agentsPage: {
      heroBadge: "Agent builder",
      title: "Design agents with clear roles and guided behavior",
      subtitle:
        "Create and refine agent profiles in a user-facing builder. Keep workspace infrastructure in Settings, and use a simple runtime check before making an agent default.",
      readinessTitle: "Readiness",
      readinessDescription: "Basic completeness for the selected agent profile.",
      readyToReview: "Ready to review",
      needsSetup: "Needs setup",
      profileName: "Profile name",
      systemPrompt: "System prompt",
      chatRouting: "Chat routing",
      chatModelReady: "Chat model ready",
      catalogTitle: "Agent catalog",
      catalogDescription: "Pick a saved profile or start a new draft.",
      new: "New",
      newDraftTitle: "New agent draft",
      newDraftDescription: "Start from workspace routing defaults.",
      draft: "Draft",
      noDescription: "No description yet.",
      default: "Default",
      builderDescription: "Guided authoring for identity, behavior, and task routing.",
      makeDefault: "Make default",
      saveAgent: "Save agent",
      tabIdentity: "Identity",
      tabBehavior: "Behavior",
      tabRouting: "Routing",
      tabPreview: "Preview",
      agentName: "Agent name",
      agentNamePlaceholder: "Policy analyst, Research operator, Ontology curator...",
      roleSummary: "Role summary",
      roleSummaryPlaceholder:
        "Describe the job this agent should own and when users should pick it.",
      allowOverride: "Allow conversation-level model override for this agent",
      promptPlaceholder:
        "Define the operating style, guardrails, and expected outputs for this agent.",
      promptHint:
        "Keep the prompt focused on role, boundaries, and output shape. Runtime policy should stay outside the prose.",
      previewTitle: "Authoring preview",
      previewDescription:
        "Fast review of what users should understand about this agent.",
      settingsTitle: "Workspace connections",
      settingsDescription:
        "Provider setup, secrets, and workspace defaults stay in Settings.",
      settingsHint:
        "Use Settings when you need to enable a provider, rotate a key, or adjust workspace defaults.",
      openSettings: "Open workspace settings",
      livePreviewTitle: "Live preview",
      livePreviewDescription:
        "Check the assigned chat model and run a simple runtime test.",
      notAssigned: "Not assigned",
      flexibleOverride: "Flexible per conversation",
      lockedOverride: "Locked to agent defaults",
      testPrompt: "Test prompt",
      retrievalEnabled: "Run with retrieval enabled",
      testAgent: "Test agent",
      lastResult: "Last runtime result",
      toolUsage: "Automation steps",
      noToolUsage: "No automation step was needed.",
      openRunDetails: "Open run details",
      viewAllRuns: "View all runs",
      recentContextTitle: "Recent profile context",
      updated: "Updated",
      unsavedDraft: "This draft has not been saved yet.",
      runtimeCheckReady: "Ready",
      needsWork: "Needs work",
    },
    askLanding: {
      newConversationTitle: "Start a new conversation",
      newConversationBody:
        "Pick an agent profile and create a chat. Model routing will come from that profile or the workspace default.",
      newConversationButton: "New conversation",
      defaultConversationTitle: "New conversation",
    },
    documentsPage: {
      title: "Documents",
      description:
        "Upload files for ingestion. Indexed chunks become available for retrieval and ontology extraction.",
    },
    ontologyPage: {
      title: "Ontology",
      description: "Published graph summary and the 5 most recent builds.",
      recentBuilds: "Recent builds",
    },
    ontologyReviewPage: {
      title: "Review queue",
      description: "All pending candidates across builds in this workspace.",
    },
    taskDetailPage: {
      backToTasks: "Back to tasks",
      title: "Task details",
      runSummaryTitle: "Run summary",
      runSummaryDescription:
        "Run metadata and output captured for this task.",
      metaTaskType: "Task type",
      metaRequestedOutput: "Requested output",
      metaWorkflow: "Workflow",
      metaProvider: "Provider",
      metaModel: "Model",
      metaUpdated: "Updated",
      unassigned: "Unassigned",
      na: "n/a",
      outputSnapshotTitle: "Output snapshot",
      errorTitle: "Error",
      toolCallsTitle: "Tool calls",
      toolCallsDescription: "Ordered history of tool activity for this task.",
      noToolCalls: "No tool call records were stored for this task.",
      colTool: "Tool",
      colStatus: "Status",
      colTrace: "Trace",
      colLatency: "Latency",
      colStarted: "Started",
      taskNotFound: "Task not found.",
      profileId: "Profile id",
    },
    placeholderPages: {
      connectors: {
        title: "Connectors",
        description:
          "External integrations (MCP, webhooks, data sources) will appear here. This area is reserved for the next release.",
      },
      artifacts: {
        title: "Artifacts",
        description:
          "Generated exports, reports, and bundles will be listed here. This area is reserved for the next release.",
      },
    },
    chat: {
      conversations: "Conversations",
      newChat: "New",
      conversationCreated: "Conversation created",
      conversationCreateFailedPrefix: "Failed to create:",
      loadConversationsFailed: "Failed to load conversations.",
      noConversationsYet: "No conversations yet. Click New to start.",
    },
    toolsPage: {
      heroBadge: "Execution primitives",
      title: "Tools",
      subtitle:
        "Browse available tools and run controlled checks when you need to validate a workflow path.",
    },
    tasksPage: {
      heroBadge: "Runtime monitor",
      title: "Tasks",
      subtitle:
        "Track task runs, inspect tool activity, and open details when a run needs review.",
      completed: "Completed",
      running: "Running",
      failed: "Failed",
      taskRuns: "Task runs",
      taskRunsDescription: "Filter by status or search by task id, task type, or workflow id.",
      searchPlaceholder: "Search task runs",
      filterStatus: "Filter status",
      statusAll: "All statuses",
      statusPending: "Pending",
      statusRunning: "Running",
      statusCompleted: "Completed",
      statusFailed: "Failed",
      noMatches: "No task runs matched the current filters.",
      tableTask: "Task",
      tableStatus: "Status",
      tableWorkflow: "Workflow",
      tableRuntime: "Runtime",
      tableUpdated: "Updated",
      tableDetails: "Details",
      unassigned: "Unassigned",
      openDetails: "Open",
    },
    workflowsPage: {
      heroBadge: "Workflow console",
      title: "Workflows",
      subtitle:
        "Review the workflow catalog, inspect recent runs, and launch controlled test runs from one place.",
      registrySnapshot: "Registry snapshot",
      registered: "Registered",
      runs: "Runs",
      registryTitle: "Workflow registry",
      registryDescription: "Deterministic and agentic workflows available in this workspace.",
      runCardTitle: "Run workflow",
      runCardDescription: "Submit a controlled test run against the selected workflow.",
      noWorkflowSelected: "No workflow selected",
      pickWorkflowFirst: "Pick a workflow from the registry first.",
      prompt: "Prompt",
      provider: "Provider",
      model: "Model",
      runButton: "Run selected workflow",
      recentRuns: "Recent runs",
      recentRunsDescription: "Filtered to the selected workflow when one is active.",
      noRunsForFilter: "No workflow runs available for this filter.",
      selectWorkflowFirstError: "Select a workflow first.",
      runSubmitted: "Workflow run submitted.",
      runFailedPrefix: "Failed to run workflow:",
      defaultPrompt: "Run a task through this workflow.",
      taskLabel: "Task",
    },
    knowledgeGraph: {
      buildsPage: {
        title: "Knowledge graph",
        subtitle:
          "Extract from indexed documents or ingest new files to publish updates. View results in the published knowledge graph.",
      },
      buildTable: {
        loadFailed: "Failed to load knowledge graph.",
        cardTitle: "Published knowledge graph",
        cardDescription:
          "Published graph summary. Run Extract on indexed documents or Ingest files to refresh results.",
        metricEntities: "Entities",
        metricRelations: "Relations",
        metricVersion: "Version",
        footerBeforeLink: "Per-build links and legacy list views are no longer shown here. See ",
        graphExplorerLink: "Graph explorer",
        footerAfterLink: " for the full published graph.",
      },
      graphStats: {
        loadFailed: "Failed to load graph.",
        publishedEntities: "Published entities",
        publishedRelations: "Published relations",
        latestVersion: "Latest version",
        buildPrefix: "build",
        entitiesSection: "Entities",
        colName: "Name",
        colType: "Type",
        colAliases: "Aliases",
        colSourceDoc: "Source doc",
        emptyEntitiesRow:
          "No published entities yet. Use Extract or Ingest on the Ontology page.",
      },
      buildDetail: {
        title: "Knowledge graph",
        description:
          "Build-level detail is no longer available in this view. Use the published graph summary. Legacy bookmark id:",
        back: "Back",
      },
      crossReview: {
        intro: "Cross-build candidate review in the old flow is no longer available.",
        codePath: "legacy review list",
        afterCode: "Use",
        extract: "Extract",
        or: "or",
        ingest: "Ingest",
        onThe: "on the",
        pageThen: "page, then inspect the published graph in",
        end: ".",
      },
      extractDialog: {
        trigger: "Extract & publish",
        title: "Extract and publish",
        description:
          "Run extraction for each selected indexed document, then publish to the graph.",
        documentsLabel: "Documents",
        selected: "Selected",
        unselected: "Select",
        noIndexedDocs: "No indexed documents. Upload and wait for indexing to finish.",
        nSelected: "document(s) selected.",
        cancel: "Cancel",
        run: "Run extract",
        running: "Running…",
        pickError: "Pick at least one document",
        toastPublished: "Extracted and published {n} document(s)",
        toastPartial: "Published {ok}, failed {fail}: {detail}",
        toastFailed: "Extract failed: {detail}",
        toastError: "Extract failed:",
      },
      ingestDialog: {
        trigger: "Ingest files",
        title: "Ingest files and publish",
        description:
          "Upload files to process and publish them to the knowledge graph.",
        chooseFiles: "Choose files",
        uploading: "Uploading…",
        close: "Close",
        toastSuccess: "Ingested {n} file(s); builds {builds}",
        toastError: "Ingest failed:",
      },
      documentCard: {
        title: "Knowledge graph",
        link: "Extract & publish",
        body: "After this document is indexed, run Extract & publish from the Ontology page to add it to the workspace graph.",
      },
    },
    evidencePage: {
      title: "Evidence",
      subtitle:
        "Search retrieval citations and published knowledge-graph entities side by side.",
      searchPlaceholder: "Search indexed chunks…",
      topKLabel: "top_k",
      search: "Search",
      sourcesLabel: "Sources",
      includeGraph: "Include published graph",
      promoteBadge: "promote: coming soon",
      empty: "Run a search or enable published graph sources to populate evidence.",
      searchFailedPrefix: "Search failed:",
      drawerSnippet: "Snippet",
      drawerProvenance: "Provenance",
      drawerLinks: "Links",
      scoreBadgePrefix: "score",
      trustBadgePrefix: "trust",
      emptyPreview: "—",
      sourceLabels: {
        retrieval: "Retrieval",
        document: "Document",
        candidateEntity: "Ontology entity",
        candidateRelation: "Ontology relation",
        graphEntity: "Graph entity",
        graphRelation: "Graph relation",
      },
      drawerSourceLabels: {
        retrieval: "Retrieval citation",
        document: "Document chunk",
        candidateEntity: "Ontology candidate entity",
        candidateRelation: "Ontology candidate relation",
        graphEntity: "Published graph entity",
        graphRelation: "Published graph relation",
      },
      openDocument: "Open document",
      openBuild: "Open build",
      externalSource: "External source",
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
    tools: {
      title: "Tools",
      table: {
        tool: "Tool",
        family: "Family",
        risk: "Risk",
        capabilities: "Capabilities",
        timeout: "Timeout",
        action: "Action",
      },
      empty: "No tools registered yet.",
      loadFailedPrefix: "Failed to load tools:",
      risk: {
        low: "Low",
        medium: "Medium",
        high: "High",
      },
      invokeDialog: {
        title: "Invoke tool",
        workspaceId: "Workspace ID",
        taskType: "Task type",
        arguments: "Arguments (JSON)",
        close: "Close",
        invoke: "Invoke tool",
        invoking: "Invoking...",
        schemaPrefix: "schema:",
        requiredPrefix: "required:",
        parseErrorPrefix: "JSON parse error:",
        argumentsObjectError: "Arguments must be a JSON object",
        status: {
          success: "Success",
          partial: "Partial",
          failed: "Failed",
        },
        results: {
          summary: "evidence · artifacts",
          hints: "hints",
          evidence: "evidence",
          artifacts: "artifacts",
          trace: "trace",
        },
        defaults: {
          workspacePlaceholder: "workspace-demo",
          taskType: "chat.retrieve",
        },
      },
    },
  },
  vi: {
    appName: "Semantic Agent",
    languageLabel: "Ngôn ngữ",
    languageOptions: {
      english: "Tiếng Anh",
      vietnamese: "Tiếng Việt",
    },
    common: {
      loading: "Đang tải...",
      close: "Đóng",
      invoke: "Thực thi",
      invoking: "Đang thực thi...",
      invokeFailed: "Thực thi thất bại:",
      cancel: "Hủy",
      upload: "Tải lên",
      uploading: "Đang tải lên...",
      uploadSelected: "Tải lên mục đã chọn",
      uploaded: "Đã tải lên",
      uploadFailedPrefix: "Tải lên thất bại:",
      uploadDescription:
        "PDF, DOCX hoặc XLSX. Chọn nhiều tệp và worker ingest sẽ xử lý theo lô.",
      file: "tệp",
      files: "tệp",
      selected: "Đã chọn",
      tags: "Nhãn",
      tagsPlaceholder: "vd: policy,2025",
      commaSeparated: "phân tách bằng dấu phẩy",
      selectAtLeastOneFile: "Chọn ít nhất một tệp để tải lên",
      failedToLoadDocuments: "Tải tài liệu thất bại.",
      noDocumentsYet: "Chưa có tài liệu nào. Hãy tải lên PDF, DOCX hoặc XLSX để bắt đầu.",
      title: "Tiêu đề",
      type: "Loại",
      status: "Trạng thái",
      chunks: "Chunks",
      updated: "Cập nhật",
      selectProfile: "Chọn hồ sơ",
      selectModel: "Chọn model",
      workspaceDefault: "Mặc định workspace",
      modelUpdateFailedPrefix: "Cập nhật model thất bại:",
      profileUpdateFailedPrefix: "Cập nhật hồ sơ thất bại:",
      sessionOverride: "Ghi đè theo phiên",
      inheritedDefault: "Kế thừa mặc định",
      profileLocksModelOverride: "Hồ sơ khóa ghi đè model",
      none: "không có",
      unknown: "không xác định",
      schema: "schema",
      required: "bắt buộc",
      evidence: "bằng chứng",
      artifacts: "artifact",
      hints: "gợi ý",
      jsonParseError: "Lỗi phân tích JSON",
      workspaceId: "Workspace ID",
      taskType: "Loại tác vụ",
      na: "n/a",
      workspaceRequired: "Hãy chọn workspace trước khi chạy thao tác này.",
      serviceUnavailable: "Không thể kết nối dịch vụ",
    },
    layout: {
      brandTagline: "Không gian làm việc cho suy luận ngữ nghĩa",
      controlPlaneLabel: "Control plane",
      logoAlt: "Logo Semantic Agent",
    },
    workspaceControlPlane: "Bảng điều khiển workspace",
    nav: {
      work: "Công việc",
      knowledge: "Tri thức",
      automation: "Tự động hóa",
      outputs: "Đầu ra",
      admin: "Quản trị",
      home: "Trang chủ",
      agents: "Agents",
      ask: "Hỏi đáp",
      documents: "Tài liệu",
      evidence: "Bằng chứng",
      ontology: "Ontology",
      graph: "Đồ thị",
      tasks: "Tác vụ",
      workflows: "Luồng công việc",
      tools: "Công cụ",
      connectors: "Kết nối",
      artifacts: "Tài sản",
      settings: "Cài đặt",
    },
    home: {
      heroBadge: "Bảng điều khiển tác nghiệp tri thức",
      title: "Không gian làm việc",
      subtitle: "Bảng điều khiển cho hỏi đáp, tài liệu, bằng chứng, ontology và đồ thị.",
      summary: {
        documents: "Tài liệu",
        graphEntities: "Thực thể đồ thị",
        conversations: "Hội thoại",
      },
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
          "Khu chạy tác vụ, danh mục workflow và tạo artifact sẽ xuất hiện ở đây khi workspace mở thêm bề mặt tự động hóa.",
      },
    },
    settingsPage: {
      title: "Cài đặt",
      description: "Các tùy chọn cấp ứng dụng sẽ nằm ở đây.",
      languageTitle: "Ngôn ngữ",
      languageDescription: "Chọn ngôn ngữ giao diện cho lớp điều khiển workspace.",
      agentProfilesTitle: "Agent profiles đã chuyển chỗ",
      agentProfilesDescription:
        "Thiết lập provider, model mặc định và quản lý agent profiles hiện nằm ở trang Agents.",
      openAgents: "Mở Agents",
    },
    agentsPage: {
      heroBadge: "Trình dựng agent",
      title: "Thiết kế agent với vai trò rõ ràng và hành vi dễ kiểm soát",
      subtitle:
        "Tạo và tinh chỉnh hồ sơ agent trong một màn hình hướng người dùng. Phần hạ tầng workspace giữ ở Cài đặt, và chỉ cần chạy thử đơn giản trước khi đặt mặc định.",
      readinessTitle: "Mức sẵn sàng",
      readinessDescription: "Mức hoàn thiện cơ bản của hồ sơ agent đang chọn.",
      readyToReview: "Đủ để rà soát",
      needsSetup: "Cần bổ sung",
      profileName: "Tên hồ sơ",
      systemPrompt: "System prompt",
      chatRouting: "Tuyến chat",
      chatModelReady: "Model chat sẵn sàng",
      catalogTitle: "Danh sách agent",
      catalogDescription: "Chọn hồ sơ đã lưu hoặc bắt đầu một bản nháp mới.",
      new: "Mới",
      newDraftTitle: "Bản nháp agent mới",
      newDraftDescription: "Bắt đầu từ cấu hình tuyến mặc định của workspace.",
      draft: "Nháp",
      noDescription: "Chưa có mô tả.",
      default: "Mặc định",
      builderDescription: "Soạn thảo có hướng dẫn cho vai trò, hành vi và tuyến tác vụ.",
      makeDefault: "Đặt mặc định",
      saveAgent: "Lưu agent",
      tabIdentity: "Danh tính",
      tabBehavior: "Hành vi",
      tabRouting: "Điều hướng",
      tabPreview: "Xem trước",
      agentName: "Tên agent",
      agentNamePlaceholder: "Chuyên viên chính sách, Điều phối nghiên cứu, Curator ontology...",
      roleSummary: "Tóm tắt vai trò",
      roleSummaryPlaceholder: "Mô tả công việc agent này nên đảm nhiệm và khi nào người dùng nên chọn nó.",
      allowOverride: "Cho phép đổi model theo từng cuộc hội thoại",
      promptPlaceholder: "Xác định phong cách làm việc, giới hạn và dạng đầu ra mong muốn cho agent này.",
      promptHint: "Giữ prompt tập trung vào vai trò, ranh giới và dạng đầu ra. Chính sách runtime nên nằm ngoài phần mô tả này.",
      previewTitle: "Xem trước nội dung",
      previewDescription: "Rà nhanh những gì người dùng sẽ hiểu về agent này.",
      settingsTitle: "Liên kết workspace",
      settingsDescription: "Provider, secret và mặc định chung vẫn nằm trong Cài đặt.",
      settingsHint: "Chỉ mở Cài đặt khi cần bật provider, thay key, hoặc đổi mặc định cấp workspace.",
      openSettings: "Mở Cài đặt workspace",
      livePreviewTitle: "Xem thử nhanh",
      livePreviewDescription: "Kiểm tra model chat đang gán và chạy thử một lượt đơn giản.",
      notAssigned: "Chưa gán",
      flexibleOverride: "Linh hoạt theo từng hội thoại",
      lockedOverride: "Giữ theo mặc định của agent",
      testPrompt: "Nội dung thử",
      retrievalEnabled: "Chạy kèm truy xuất tài liệu",
      testAgent: "Chạy thử agent",
      lastResult: "Kết quả gần nhất",
      toolUsage: "Các bước tự động",
      noToolUsage: "Không cần bước tự động nào.",
      openRunDetails: "Mở chi tiết lượt chạy",
      viewAllRuns: "Xem mọi lượt chạy",
      recentContextTitle: "Ngữ cảnh gần đây",
      updated: "Cập nhật",
      unsavedDraft: "Bản nháp này chưa được lưu.",
      runtimeCheckReady: "Sẵn sàng",
      needsWork: "Cần chỉnh thêm",
    },
    askLanding: {
      newConversationTitle: "Bắt đầu hội thoại mới",
      newConversationBody:
        "Chọn hồ sơ agent rồi tạo cuộc chat. Model routing sẽ lấy từ hồ sơ đó hoặc mặc định workspace.",
      newConversationButton: "Hội thoại mới",
      defaultConversationTitle: "Hội thoại mới",
    },
    documentsPage: {
      title: "Tài liệu",
      description:
        "Tải tệp để ingest. Các chunk đã index sẽ dùng được cho truy xuất và trích xuất ontology.",
    },
    ontologyPage: {
      title: "Ontology",
      description: "Tổng quan đồ thị đã xuất bản và 5 build gần nhất.",
      recentBuilds: "Build gần đây",
    },
    ontologyReviewPage: {
      title: "Hàng đợi duyệt",
      description: "Tất cả ứng viên đang chờ duyệt từ các build trong workspace này.",
    },
    taskDetailPage: {
      backToTasks: "Quay lại tác vụ",
      title: "Chi tiết tác vụ",
      runSummaryTitle: "Tóm tắt lần chạy",
      runSummaryDescription:
        "Metadata và đầu ra được ghi nhận cho lần chạy này.",
      metaTaskType: "Loại tác vụ",
      metaRequestedOutput: "Đầu ra yêu cầu",
      metaWorkflow: "Workflow",
      metaProvider: "Provider",
      metaModel: "Model",
      metaUpdated: "Cập nhật",
      unassigned: "Chưa gán",
      na: "n/a",
      outputSnapshotTitle: "Ảnh chụp đầu ra",
      errorTitle: "Lỗi",
      toolCallsTitle: "Tool calls",
      toolCallsDescription: "Lịch sử theo thứ tự của các lần gọi công cụ trong tác vụ này.",
      noToolCalls: "Không có bản ghi tool call cho tác vụ này.",
      colTool: "Công cụ",
      colStatus: "Trạng thái",
      colTrace: "Trace",
      colLatency: "Độ trễ",
      colStarted: "Bắt đầu",
      taskNotFound: "Không tìm thấy tác vụ.",
      profileId: "Mã hồ sơ",
    },
    placeholderPages: {
      connectors: {
        title: "Kết nối",
        description:
          "Tích hợp bên ngoài (MCP, webhook, nguồn dữ liệu) sẽ hiển thị tại đây. Khu vực này dành cho bản phát hành tiếp theo.",
      },
      artifacts: {
        title: "Tài sản đầu ra",
        description:
          "Bản xuất, báo cáo và gói đã tạo sẽ được liệt kê tại đây. Khu vực này dành cho bản phát hành tiếp theo.",
      },
    },
    chat: {
      conversations: "Hội thoại",
      newChat: "Mới",
      conversationCreated: "Đã tạo hội thoại",
      conversationCreateFailedPrefix: "Tạo thất bại:",
      loadConversationsFailed: "Tải danh sách hội thoại thất bại.",
      noConversationsYet: "Chưa có hội thoại. Nhấn Mới để bắt đầu.",
    },
    toolsPage: {
      heroBadge: "Nguyên thực thi",
      title: "Công cụ",
      subtitle:
        "Duyệt các công cụ sẵn có và chạy kiểm tra có kiểm soát khi cần xác minh luồng xử lý.",
    },
    tasksPage: {
      heroBadge: "Giám sát runtime",
      title: "Tác vụ",
      subtitle:
        "Theo dõi các lần chạy tác vụ, xem hoạt động công cụ và mở chi tiết khi cần review.",
      completed: "Hoàn thành",
      running: "Đang chạy",
      failed: "Thất bại",
      taskRuns: "Các lần chạy",
      taskRunsDescription: "Lọc theo trạng thái hoặc tìm theo id tác vụ, loại, hoặc workflow.",
      searchPlaceholder: "Tìm lần chạy",
      filterStatus: "Lọc trạng thái",
      statusAll: "Mọi trạng thái",
      statusPending: "Chờ",
      statusRunning: "Đang chạy",
      statusCompleted: "Hoàn thành",
      statusFailed: "Thất bại",
      noMatches: "Không có lần chạy nào khớp bộ lọc.",
      tableTask: "Tác vụ",
      tableStatus: "Trạng thái",
      tableWorkflow: "Workflow",
      tableRuntime: "Runtime",
      tableUpdated: "Cập nhật",
      tableDetails: "Chi tiết",
      unassigned: "Chưa gán",
      openDetails: "Mở",
    },
    workflowsPage: {
      heroBadge: "Bảng điều khiển workflow",
      title: "Luồng công việc",
      subtitle:
        "Xem danh mục workflow, các lần chạy gần đây và kích hoạt chạy thử có kiểm soát trong một nơi.",
      registrySnapshot: "Tổng quan registry",
      registered: "Đã đăng ký",
      runs: "Lần chạy",
      registryTitle: "Registry workflow",
      registryDescription: "Các workflow xác định và agentic hiện có trong workspace.",
      runCardTitle: "Chạy workflow",
      runCardDescription: "Gửi một lần chạy thử có kiểm soát cho workflow đã chọn.",
      noWorkflowSelected: "Chưa chọn workflow",
      pickWorkflowFirst: "Hãy chọn một workflow trong registry trước.",
      prompt: "Prompt",
      provider: "Provider",
      model: "Model",
      runButton: "Chạy workflow đã chọn",
      recentRuns: "Lần chạy gần đây",
      recentRunsDescription: "Lọc theo workflow đang chọn khi có.",
      noRunsForFilter: "Không có lần chạy nào cho bộ lọc này.",
      selectWorkflowFirstError: "Hãy chọn workflow trước.",
      runSubmitted: "Đã gửi chạy workflow.",
      runFailedPrefix: "Chạy workflow thất bại:",
      defaultPrompt: "Chạy một tác vụ qua workflow này.",
      taskLabel: "Tác vụ",
    },
    knowledgeGraph: {
      buildsPage: {
        title: "Đồ thị tri thức",
        subtitle:
          "Trích xuất từ tài liệu đã index hoặc nạp file mới để cập nhật và xuất bản. Xem kết quả trong đồ thị tri thức đã xuất bản.",
      },
      buildTable: {
        loadFailed: "Tải đồ thị tri thức thất bại.",
        cardTitle: "Đồ thị tri thức đã xuất bản",
        cardDescription:
          "Tóm tắt đồ thị đã xuất bản. Chạy Trích xuất trên tài liệu đã index hoặc Nạp file để làm mới dữ liệu.",
        metricEntities: "Thực thể",
        metricRelations: "Quan hệ",
        metricVersion: "Phiên bản",
        footerBeforeLink: "Liên kết theo từng build và các màn hình danh sách cũ không còn hiển thị tại đây. Xem ",
        graphExplorerLink: "Trình khám phá đồ thị",
        footerAfterLink: " cho bản đồ đầy đủ.",
      },
      graphStats: {
        loadFailed: "Tải đồ thị thất bại.",
        publishedEntities: "Thực thể đã xuất bản",
        publishedRelations: "Quan hệ đã xuất bản",
        latestVersion: "Phiên bản mới nhất",
        buildPrefix: "build",
        entitiesSection: "Thực thể",
        colName: "Tên",
        colType: "Loại",
        colAliases: "Bí danh",
        colSourceDoc: "Tài liệu nguồn",
        emptyEntitiesRow:
          "Chưa có thực thể đã xuất bản. Hãy dùng Trích xuất hoặc Nạp file trên trang Ontology.",
      },
      buildDetail: {
        title: "Đồ thị tri thức",
        description:
          "Chi tiết theo từng build không còn hiển thị trong màn này. Hãy dùng phần tóm tắt đồ thị đã xuất bản. Id bookmark cũ:",
        back: "Quay lại",
      },
      crossReview: {
        intro: "Luồng duyệt chéo ứng viên giữa các build trước đây không còn khả dụng.",
        codePath: "màn danh sách cũ",
        afterCode: "Hãy dùng",
        extract: "Trích xuất",
        or: "hoặc",
        ingest: "Nạp file",
        onThe: "trên trang",
        pageThen: "rồi xem đồ thị đã xuất bản tại",
        end: ".",
      },
      extractDialog: {
        trigger: "Trích xuất & xuất bản",
        title: "Trích xuất và xuất bản",
        description:
          "Chạy trích xuất cho từng tài liệu đã chọn, sau đó xuất bản lên đồ thị.",
        documentsLabel: "Tài liệu",
        selected: "Đã chọn",
        unselected: "Chọn",
        noIndexedDocs: "Chưa có tài liệu đã index. Hãy tải lên và chờ index xong.",
        nSelected: "tài liệu đã chọn.",
        cancel: "Hủy",
        run: "Chạy trích xuất",
        running: "Đang chạy…",
        pickError: "Chọn ít nhất một tài liệu",
        toastPublished: "Đã trích xuất và xuất bản {n} tài liệu",
        toastPartial: "Đã xuất bản {ok}, thất bại {fail}: {detail}",
        toastFailed: "Trích xuất thất bại: {detail}",
        toastError: "Trích xuất thất bại:",
      },
      ingestDialog: {
        trigger: "Nạp file",
        title: "Nạp file và xuất bản",
        description:
          "Tải file để xử lý và xuất bản lên đồ thị tri thức.",
        chooseFiles: "Chọn file",
        uploading: "Đang tải…",
        close: "Đóng",
        toastSuccess: "Đã nạp {n} file; build {builds}",
        toastError: "Nạp thất bại:",
      },
      documentCard: {
        title: "Đồ thị tri thức",
        link: "Trích xuất & xuất bản",
        body: "Sau khi tài liệu được index, chạy Trích xuất & xuất bản từ trang Ontology để đưa vào đồ thị workspace.",
      },
    },
    evidencePage: {
      title: "Bằng chứng",
      subtitle:
        "Tìm trích dẫn retrieval và thực thể đồ thị đã xuất bản song song.",
      searchPlaceholder: "Tìm trong chunk đã index…",
      topKLabel: "top_k",
      search: "Tìm",
      sourcesLabel: "Nguồn",
      includeGraph: "Gồm dữ liệu đồ thị đã xuất bản",
      promoteBadge: "thăng cấp: sắp có",
      empty: "Chạy tìm hoặc bật nguồn đồ thị để hiển thị bằng chứng.",
      searchFailedPrefix: "Tìm thất bại:",
      drawerSnippet: "Đoạn trích",
      drawerProvenance: "Nguồn gốc",
      drawerLinks: "Liên kết",
      scoreBadgePrefix: "điểm",
      trustBadgePrefix: "tin cậy",
      emptyPreview: "—",
      sourceLabels: {
        retrieval: "Truy xuất",
        document: "Tài liệu",
        candidateEntity: "Thực thể ontology",
        candidateRelation: "Quan hệ ontology",
        graphEntity: "Thực thể đồ thị",
        graphRelation: "Quan hệ đồ thị",
      },
      drawerSourceLabels: {
        retrieval: "Trích dẫn truy xuất",
        document: "Chunk tài liệu",
        candidateEntity: "Thực thể ứng viên ontology",
        candidateRelation: "Quan hệ ứng viên ontology",
        graphEntity: "Thực thể đồ thị đã xuất bản",
        graphRelation: "Quan hệ đồ thị đã xuất bản",
      },
      openDocument: "Mở tài liệu",
      openBuild: "Mở build",
      externalSource: "Nguồn ngoài",
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
    tools: {
      title: "Công cụ",
      table: {
        tool: "Công cụ",
        family: "Nhóm",
        risk: "Rủi ro",
        capabilities: "Khả năng",
        timeout: "Timeout",
        action: "Hành động",
      },
      empty: "Chưa có công cụ nào được đăng ký.",
      loadFailedPrefix: "Tải công cụ thất bại:",
      risk: {
        low: "Thấp",
        medium: "Trung bình",
        high: "Cao",
      },
      invokeDialog: {
        title: "Thực thi công cụ",
        workspaceId: "Workspace ID",
        taskType: "Loại tác vụ",
        arguments: "Tham số (JSON)",
        close: "Đóng",
        invoke: "Thực thi công cụ",
        invoking: "Đang thực thi...",
        schemaPrefix: "schema:",
        requiredPrefix: "bắt buộc:",
        parseErrorPrefix: "Lỗi phân tích JSON:",
        argumentsObjectError: "Arguments phải là một JSON object",
        status: {
          success: "Thành công",
          partial: "Một phần",
          failed: "Thất bại",
        },
        results: {
          summary: "bằng chứng · artifact",
          hints: "gợi ý",
          evidence: "bằng chứng",
          artifacts: "artifact",
          trace: "trace",
        },
        defaults: {
          workspacePlaceholder: "workspace-demo",
          taskType: "chat.retrieve",
        },
      },
    },
  },
};
