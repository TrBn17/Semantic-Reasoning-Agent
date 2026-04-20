# AGENTS Ontology Architecture

## Muc tieu

Tai lieu nay tong hop cach `MiroFish_vie` dang tao ontology tren source that, sau do de xuat plan cho `Semantic-Reasoning-Agent` de mo phong theo tinh than cua ho nhung van dung voi PRD hien tai: tool-first, workflow-centric, ontology-guided.

Ket luan ngan:

- `MiroFish_vie` khong dung multi-agent runtime de tao ontology.
- Ho dung mot pipeline 2 pha rat ro rang:
  1. `generate_ontology`: upload file -> trich text -> goi 1 LLM prompt sinh JSON ontology.
  2. `build_graph`: dung ontology da sinh de cau hinh graph backend, chunk text, nap text vao graph engine, cho graph engine rut trich node/edge.
- Phan "agents" cua ho nam o simulation/report, khong nam trong ontology generation.
- Dieu dang hoc tu ho la tach ontology design ra khoi graph build, giu project state ro rang, va xem ontology la contract truoc khi ingest vao graph.
- Dieu khong nen copy nguyen xi la: single-shot ontology prompt, thieu provenance/evidence contract, thieu review queue chat, va su phu thuoc chat vao graph vendor.

## Pham vi nghien cuu

Da doc va doi chieu cac phan sau:

- `MiroFish_vie/backend/app/api/graph.py`
- `MiroFish_vie/backend/app/services/ontology_generator.py`
- `MiroFish_vie/backend/app/services/graph_builder.py`
- `MiroFish_vie/backend/app/models/project.py`
- `MiroFish_vie/backend/app/utils/file_parser.py`
- `MiroFish_vie/backend/app/services/text_processor.py`

Va doi chieu voi code hien tai cua repo nay:

- `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py`
- `apps/backend/src/semantic_reasoning_agent/services/workflow_runtime.py`
- `apps/backend/src/semantic_reasoning_agent/services/tool_runtime.py`
- `apps/backend/src/semantic_reasoning_agent/services/ontology_service.py`
- `apps/backend/src/semantic_reasoning_agent/infrastructure/ontology/llm_extractor.py`
- `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py`
- `apps/backend/src/semantic_reasoning_agent/domain/contracts/evidence.py`

Co thu dung GitNexus MCP de truy execution flow. Repo `MiroFish_vie` da duoc index, nhung mot so lenh `context()` bi lock file tranh chap trong luc doc index, nen phan ket luan chu yeu duoc xac nhan bang source code truc tiep. Phan GitNexus tren repo hien tai van huu ich de xac nhan `TaskRuntime` va `WorkflowRuntime` da co seam can thiet cho giai doan tiep theo.

## 1. MiroFish_vie dang tao ontology nhu the nao

## 1.1 Entry API va operating model

Backend cua `MiroFish_vie` to chuc ontology/graph thanh 2 API rieng:

- `POST /api/graph/ontology/generate`
- `POST /api/graph/build`

Day la diem dung ve mat kien truc:

- ontology duoc sinh truoc, co the xem nhu mot artifact trung gian;
- graph build chi duoc chay sau khi ontology da ton tai;
- project state duoc luu server-side, frontend khong phai truyen lai payload lon.

Project state duoc luu qua `ProjectManager` trong thu muc upload:

- file goc
- extracted text
- ontology JSON
- graph id
- task id
- trang thai `created -> ontology_generated -> graph_building -> graph_completed|failed`

Mo hinh nay rat don gian nhung de van hanh.

## 1.2 Pipeline ontology that su

Luong `generate_ontology` trong `MiroFish_vie/backend/app/api/graph.py` la:

1. Nhan `simulation_requirement`, `project_name`, `additional_context`, `files`.
2. Tao `project`.
3. Luu file vao project folder.
4. Parse tung file thanh text.
5. Tien xu ly text.
6. Gop text cac tai lieu thanh mot blob lon.
7. Goi `OntologyGenerator.generate(...)`.
8. Luu `entity_types`, `edge_types`, `analysis_summary` vao project.

Khong co:

- tool registry
- workflow registry
- review queue cho ontology types
- evidence-level provenance
- multi-step sufficiency/conflict gate

No la mot synchronous design step, khong phai ontology extraction pipeline day du.

## 1.3 Agent dung o day la "mot LLM prompt", khong phai multi-agent

`OntologyGenerator` trong `MiroFish_vie/backend/app/services/ontology_generator.py` thuc chat:

- build 1 system prompt rat dai;
- nhan `document_texts + simulation_requirement + additional_context`;
- cat text neu vuot `MAX_TEXT_LENGTH_FOR_LLM`;
- goi `LLMClient.chat_json(...)`;
- validate va patch ket qua.

Co 3 dac diem quan trong:

1. Ontology duoc sinh o muc type-system, khong phai muc instance extraction.
2. Prompt buoc model tao:
   - `entity_types`
   - `edge_types`
   - `analysis_summary`
3. Hau xu ly ep them fallback `Person` va `Organization`, va cat so luong type theo gioi han graph vendor.

Noi cach khac, "agent tao ontology" cua ho la:

- 1 planning/generation agent
- 1 lan goi
- output la ontology schema JSON
- khong co debate, critic, planner-worker, hay review agent

## 1.4 Ontology la contract cho graph vendor

Sau khi sinh ontology, `GraphBuilderService.set_ontology(...)` se:

- doc `entity_types` va `edge_types`;
- tao dynamic Pydantic/Zep classes;
- remap reserved attributes;
- build `source_targets`;
- goi API graph vendor de set ontology.

Graph build sau do:

1. tao graph id;
2. set ontology;
3. split text;
4. add text batches vao graph engine;
5. poll episodes cho toi khi graph engine process xong;
6. doc nodes/edges da trich xuat tu graph.

Y nghia kien truc:

- ontology cua ho khong phai graph output;
- ontology la schema/constraint input cho graph extraction.

Day la diem rat dang hoc.

## 1.5 Parser va chunking ben ho

Parser:

- PDF: `PyMuPDF`
- Markdown/TXT: doc text thuan

Chunking:

- split theo character window voi overlap;
- co co gang tim sentence boundary, nhung van la chunking kha tho.

Diem manh:

- de trien khai;
- du nhanh de tao graph vendor input.

Diem yeu:

- chunking khong giu anchor giau ngu nghia;
- parser contract va provenance rat mong;
- ontology generation khong dua tren chunks co anchor, ma dua tren text da gop.

## 1.6 Phan "Agent" thuc su cua MiroFish_vie nam o dau

Trong repo nay, "agentic" manh hon nam o:

- `report_agent.py`
- `zep_tools.py`
- simulation interview flow
- profile/config generation cho OASIS agents

Nhung cac phan do khong tao ontology. Chung dung ontology/graph da xay xong de phuc vu simulation, retrieval va report.

Vi vay, neu noi chinh xac:

- `MiroFish_vie` la ontology-first, graph-assisted simulation platform.
- Nhung ontology creation cua ho chua phai agent runtime; no la LLM-assisted schema design.

## 2. Bai hoc kien truc co the muon hoc theo

## 2.1 Cac diem nen hoc

### A. Tach `ontology design` khoi `graph build`

Day la bai hoc lon nhat.

Trong repo cua ta, ontology build hien tai da co build/publish state trong `OntologyService`, nhung van thieu mot lop "ontology architecture artifact" ro rang o runtime answer/task flow. MiroFish cho thay:

- ontology nen duoc xem la mot ket qua trung gian co the inspect;
- graph publish/index la pha sau;
- frontend/backend co the theo doi state cua tung pha tach biet.

### B. Dung ontology nhu execution contract, khong chi la output

Ben ho:

- ontology schema duoc set truoc khi graph engine nhan text.

Ben ta:

- PRD da noi ontology la semantic control layer;
- ta nen day manh hon phan nay bang cach cho workflow/tool chay dua tren ontology context, ontology schema, va review rules.

### C. Giu project/build state ben server

MiroFish luu `project` dung de tranh lap lai payload giua cac API. Repo ta da co `OntologyBuildORM`, `OntologyBuildStepORM`, `OntologyVersionORM`; can tiep tuc mo rong theo huong:

- task run
- workflow run
- ontology architecture artifact
- evidence promotion state
- review state

### D. Cho user nhin thay ontology truoc khi publish

Ho khong co review queue sau, nhung ve UX/process thi van co "ontology first, graph later". Ta nen lam ban nang cap:

- sinh schema candidates;
- cho review/policy auto-approve;
- roi moi publish/sync graph.

## 2.2 Cac diem khong nen hoc nguyen xi

### A. Khong nen dung single-shot prompt lam center

PRD cua ta khong cho phep he thong ontology phu thuoc mot prompt schema duy nhat. Ly do:

- khong du provenance;
- kho conflict-check;
- kho review;
- kho merge multi-document;
- kho map vao evidence contract.

### B. Khong nen de graph vendor dinh nghia boundary nghiep vu

Ben ho, ontology bi shape boi gioi han graph vendor:

- max entity types
- max edge types
- reserved field names

Ben ta, ontology phai do domain va review workflow quyet dinh. Graph projection chi la derived representation.

### C. Khong nen bo qua evidence-level contracts

MiroFish sinh ontology type-system tu blob text tong hop. Ta can giu:

- chunk-level evidence
- citation anchor
- provenance
- confidence
- review status

vi day la xuong song cua PRD.

### D. Khong nen nham "ontology design" voi "entity extraction"

MiroFish gop ca hai y niem:

- tao schema types
- sau do de graph engine tu extract instances

Repo ta hien da di xa hon:

- `OntologyService` da co candidate entities/relations
- published versions
- review status

Vi vay ta nen giu 2 tang ro rang:

1. ontology schema architecture
2. ontology candidate extraction/publish

## 3. Doi chieu voi backend hien tai cua chung ta

## 3.1 Chung ta da co nhung seam tot hon MiroFish

Repo hien tai da co cac thanh phan ma `MiroFish_vie` chua co:

- `ToolRegistry`
- `ToolRuntime`
- `TaskRuntime`
- `WorkflowRuntime`
- `ToolEnvelope` / `ToolResult`
- `Evidence` contract
- `OntologyService` voi build/review/publish state
- `OpenDomainLLMExtractor` sau ontology extraction port

Noi cach khac:

- MiroFish co operating shape hay.
- Chung ta co backend seam dung hon cho mot ontology runtime thuc su.

## 3.2 Chung ta dang thieu gi neu muon "mo phong theo cach ho"

Nhung khoang trong chinh:

### A. Chua co pha "ontology architecture/design" tach biet

Hien tai ontology extractor cua ta di thang vao:

- classify domain
- extract entities
- extract relations
- resolve
- publish/sync

Ta chua co artifact rieng cho:

- de xuat entity types
- de xuat relation types
- de xuat normalization rules
- de xuat review policy hints
- de xuat tool affinity/workflow hints

Tuc la ta chua co lop tuong duong pha `generate_ontology` cua MiroFish, nhung o phien ban manh hon.

### B. `TaskRuntime` moi o muc "tool-enabled chat resolution"

`TaskRuntime` hien:

- chon workflow don gian;
- cho LLM goi tools;
- fallback retrieval;
- dung ontology graph published lam context hint.

No chua co:

- ontology grounding stage doc lap;
- workflow selection dua tren ontology architecture;
- sufficiency/conflict gates that su;
- task output class doi tu answer sang review/artifact/graph update.

### C. Chua co tool family cho ontology architecture

Hien co:

- `retrieval.internal`
- `ontology.lookup`

Nhung chua co:

- `ontology.design`
- `ontology.candidate_extract`
- `ontology.normalize`
- `ontology.review_route`
- `graph.publish`
- `evidence.promote`

### D. Chua co persistence cho runtime-side ontology design artifacts

Can bo sung bang/tai lieu cho:

- ontology schema drafts
- ontology grounding snapshots
- tool-call linked schema proposals
- evidence-to-schema links

## 4. De xuat architecture cho AGENTS ontology cua chung ta

## 4.1 Nguyen tac thiet ke

Ta khong copy pipeline cua MiroFish 1:1.

Ta se mo phong theo 4 nguyen tac cua ho, nhung nang cap dung voi PRD:

1. `Ontology design` la pha doc lap, co artifact ro rang.
2. `Ontology extraction/build` dung artifact do lam runtime contract.
3. `Graph publish` la pha sau, khong tron vao extraction.
4. `Agents` duoc dung de lap ke hoach, phan tich, va review ontology; khong phai chi de chat.

## 4.2 Kien truc muc cao de xuat

```text
Document(s) / Task
  -> Retrieval + parse/chunk anchors
  -> Ontology Design Workflow
      -> ontology.design tool
      -> ontology.review_route tool
      -> ontology.schema_draft artifact
  -> Ontology Candidate Workflow
      -> ontology.candidate_extract tool
      -> ontology.normalize tool
      -> candidate entities/relations + evidence links
  -> Review / Approval Workflow
      -> approve/merge/reject
  -> Graph Publish Workflow
      -> graph.publish tool
      -> Neo4j projection / published ontology graph
  -> Runtime Consumption
      -> task grounding
      -> tool selection
      -> answer / artifact / review task / graph update request
```

## 4.3 "Agent" nen duoc dung o dau

Neu user muon "su dung Agents tao ontology", cach dung hop ly trong repo nay la:

### Agent 1: Ontology Architect

Nhiem vu:

- doc evidence/chunks;
- de xuat domain;
- de xuat entity types;
- de xuat relation types;
- de xuat normalization rules;
- de xuat review rules;
- de xuat workflow/tool affinity hints.

Output:

- `OntologyArchitectureDraft`

### Agent 2: Ontology Critic/Reviewer

Nhiem vu:

- tim overlap type;
- tim abstract types khong nen ton tai;
- tim relation type mo ho;
- kiem tra coverage theo evidence;
- danh dau cho nao can review nguoi.

Output:

- `OntologyArchitectureReview`

### Agent 3: Candidate Extractor

Nhiem vu:

- dung architecture draft da approved de extract entities/relations tu chunks;
- gan evidence anchors;
- sinh candidate records.

Output:

- `ExtractedEntity[]`
- `ExtractedRelation[]`

### Agent 4: Resolver/Normalizer

Nhiem vu:

- canonicalize ten;
- merge aliases;
- ap ontology constraints;
- route ambiguous merges sang review.

Output:

- normalized candidates
- merge plan

Luu y:

- Day khong nhat thiet la 4 process LLM song song ngay lap tuc.
- O phase dau, co the trien khai thanh 2 buoc LLM noi bo trong deterministic workflow.
- Quan trong la phan tach responsibility, khong phai nhat thiet phai dung framework agent phuc tap.

## 5. Contract moi can them

## 5.1 OntologyArchitectureDraft

Can them 1 contract moi, vi day la artifact ma repo hien tai chua co.

Goi y:

```json
{
  "draft_id": "string",
  "workspace_id": "string",
  "source_document_ids": ["string"],
  "domain": "string",
  "entity_types": [
    {
      "name": "string",
      "description": "string",
      "attributes": [],
      "normalization_hints": [],
      "evidence_refs": []
    }
  ],
  "relation_types": [
    {
      "name": "string",
      "description": "string",
      "source_targets": [],
      "evidence_refs": []
    }
  ],
  "review_rules": [],
  "tool_affinity_hints": [],
  "workflow_hints": [],
  "provenance": {},
  "status": "draft | reviewed | approved | rejected"
}
```

Khac voi MiroFish:

- co evidence refs;
- co provenance;
- co status/review;
- khong bi rang buoc boi graph vendor.

## 5.2 Evidence-to-schema link

Can bo sung lien ket tu `Evidence` sang schema draft:

- evidence nao ho tro entity type nao
- evidence nao ho tro relation type nao
- evidence nao gay conflict

Day la phan then chot de ontology thuc su "guided by evidence", khong phai chi "prompt-generated".

## 5.3 Tool contracts moi

De xuat dang ky them:

- `ontology.design`
- `ontology.review`
- `ontology.extract_candidates`
- `ontology.normalize_candidates`
- `ontology.publish_graph`

Moi tool phai tra ve `ToolResult` theo contract hien tai.

## 6. Workflow de xuat

## 6.1 Workflow 1: `ontology_design`

Mode:

- deterministic, co the chua 1-2 LLM-backed steps

Input:

- workspace id
- document ids
- optional task intent

Steps:

1. lay chunks/evidence dai dien
2. goi `ontology.design`
3. goi `ontology.review`
4. luu `OntologyArchitectureDraft`
5. route review neu can

Output:

- architecture draft
- review flags

Y nghia:

- day la buoc tuong duong `generate_ontology` cua MiroFish, nhung dung contract va provenance dung hon.

## 6.2 Workflow 2: `ontology_candidate_build`

Mode:

- deterministic

Steps:

1. nap architecture draft da approved
2. lay source chunks
3. extract candidate entities/relations
4. normalize/resolution
5. luu candidate + evidence links

Output:

- candidate entities
- candidate relations

## 6.3 Workflow 3: `ontology_review_publish`

Mode:

- deterministic

Steps:

1. lay candidate approved
2. tao published version
3. sync graph projection
4. cap nhat runtime semantic assets

Output:

- published ontology version
- graph sync result

## 6.4 Workflow 4: `task_resolve_with_ontology`

Mode:

- agentic

Steps:

1. interpret task
2. lay ontology context + architecture draft gan nhat
3. chon workflow
4. chon tools
5. sufficiency/conflict gate
6. answer / review task / graph update request / artifact

Output:

- phu hop voi PRD, khong bi gioi han vao answer.

## 7. Mapping cu the vao codebase hien tai

## 7.1 Cac file/service nen them hoac mo rong

### A. Domain contracts

Them:

- `domain/contracts/ontology_architecture.py`

Chua:

- `OntologyArchitectureDraft`
- `OntologyArchitectureReview`
- `SchemaEvidenceLink`

### B. Persistence

Them:

- `persistence/models/ontology_architecture.py`
- repository ho tro luu draft/review/version

Bang goi y:

- `ontology_schema_drafts`
- `ontology_schema_reviews`
- `ontology_schema_evidence_links`

### C. Tools

Them:

- `tools/ontology/ontology_design_tool.py`
- `tools/ontology/ontology_review_tool.py`
- `tools/ontology/ontology_extract_candidates_tool.py`
- `tools/graph/graph_publish_tool.py`

### D. Services

Mo rong:

- `services/tool_registry.py`
- `services/task_runtime.py`
- `services/workflow_runtime.py`
- `services/ontology_service.py`

Them:

- `services/ontology_architecture_service.py`
- `services/ontology_grounding_service.py`

### E. LLM infrastructure

Them:

- `infrastructure/ontology/architecture_prompts.py`
- co the tach prompt cho:
  - architect
  - critic
  - extractor

## 7.2 Mapping vao workflow runtime hien co

`WorkflowRuntime` da co registry va run audit. Can nang cap bang:

- them workflow `ontology_design`
- them workflow `ontology_candidate_build`
- them workflow `ontology_review_publish`

`TaskRuntime` can doi tu:

- "LLM co the goi tools trong chat"

thanh:

- "task duoc ground boi ontology va route vao workflow phu hop"

Buoc thay doi cu the:

1. Chen `ontology_grounding` truoc `_select_workflow`.
2. `_select_workflow` doc:
   - requested output
   - ontology domain
   - schema draft availability
   - freshness/web policy
3. `_select_tools` doc them:
   - workflow policy
   - ontology architecture hints
4. Cho phep terminal outputs khac `answer`.

## 7.3 Mapping vao OntologyService hien co

`OntologyService` da co phan build/review/publish rat tot. Nen giu va chen them 1 lop truoc no:

- `ontology architecture design`

De xuat trach nhiem moi:

- `OntologyArchitectureService`
  - tao draft
  - review draft
  - approve draft
  - tra ve active draft theo workspace/domain

- `OntologyService`
  - dung active draft khi extract candidates
  - dung draft rules khi resolve/merge
  - publish versions nhu hien tai

Day la cach "mo phong theo MiroFish" ma khong lam vo PRD hien tai.

## 8. Phase implementation de xuat

## Phase 1: Tao lop ontology architecture draft

Muc tieu:

- co artifact tuong duong pha `generate_ontology` cua MiroFish

Cong viec:

1. them contract + persistence cho `OntologyArchitectureDraft`
2. them `ontology.design` tool
3. them `OntologyArchitectureService`
4. them API:
   - `POST /api/v1/ontology/architecture/design`
   - `GET /api/v1/ontology/architecture/{draft_id}`
   - `POST /api/v1/ontology/architecture/{draft_id}/review`

Definition of done:

- co the tao ontology schema draft tu document da index;
- draft co provenance + evidence refs;
- draft co review status.

## Phase 2: Ghep draft vao ontology extraction pipeline

Muc tieu:

- candidate extraction khong con open-ended hoan toan

Cong viec:

1. cap nhat `OpenDomainLLMExtractor` de nhan active draft
2. prompt extraction dung:
   - known entity types
   - known relation types
   - normalization rules
3. luu evidence-to-schema links
4. cap nhat `OntologyService.process_build(...)` de load architecture draft truoc khi extract

Definition of done:

- 1 build ontology co the trace nguoc:
  - candidate -> evidence
  - candidate -> schema draft
  - schema draft -> source docs

## Phase 3: Day ontology vao TaskRuntime

Muc tieu:

- ontology tro thanh control layer dung nghia PRD

Cong viec:

1. them `OntologyGroundingService`
2. bo sung `ontology_grounding` snapshot vao task run
3. cap nhat `_select_workflow`
4. cap nhat `_select_tools`
5. them cac output class:
   - `review_task`
   - `ontology_candidates`
   - `graph_update_request`

Definition of done:

- task runtime co the route khac nhau dua tren ontology context, khong chi dua tren raw user message.

## Phase 4: Publish va graph projection policy

Muc tieu:

- giu tinh than "ontology first, graph later"

Cong viec:

1. them `graph.publish` tool
2. buoc publish doc approved candidates + approved architecture
3. cap nhat audit trail cho graph sync
4. dam bao graph projection la derived, rebuildable

Definition of done:

- co workflow publish tach biet, khong tron voi extraction.

## Phase 5: Agentic critic va conflict gating

Muc tieu:

- nang cap tu LLM-assisted sang ontology-agent workflow thuc su

Cong viec:

1. them `ontology.review` tool/step
2. them conflict heuristics:
   - type overlap
   - relation ambiguity
   - low evidence support
3. route build sang review neu confidence thap

Definition of done:

- he thong biet khi nao khong nen auto-publish/auto-answer.

## 9. Kien nghi implementation cu the, uu tien cao

Neu muon di nhanh va dung huong, toi de xuat thu tu:

1. Lam `OntologyArchitectureDraft` truoc.
2. Tich hop draft vao `OntologyService`.
3. Sau do moi day vao `TaskRuntime`.

Ly do:

- Day la phan gan nhat voi bai hoc tu MiroFish.
- No bo sung mot lop hien dang thieu trong repo.
- No khong pha vo cac seam da ship o PR-3.
- No dat nen cho agentic ontology that su o cac phase sau.

## 10. Ket luan thiet ke

Neu muon "mo phong theo MiroFish_vie", cach dung nhat khong phai la copy prompt `OntologyGenerator` cua ho.

Cach dung nhat la hoc 3 y tuong:

1. ontology phai duoc tao ra truoc nhu mot artifact doc lap;
2. graph build/publish phai la pha sau va phu thuoc ontology do;
3. system state phai nhin thay tung pha ro rang.

Con cach trien khai trong repo cua ta nen vuot len tren MiroFish bang:

- tool contracts
- workflow runtime
- evidence/provenance
- review/publish gates
- ontology-guided task routing

Tom lai:

- `MiroFish_vie` cho ta hinh dang san pham dung.
- `Semantic-Reasoning-Agent` da co backend seam tot hon de bien no thanh ontology runtime dung nghia.
- Phase tiep theo nen la them `ontology architecture draft` lam cau noi giua document evidence va ontology candidate/publish pipeline.
