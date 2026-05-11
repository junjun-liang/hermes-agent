# Hermes Agent - Detailed Flowcharts (Mermaid)

## 1. 核心对话循环 (Core Conversation Loop)

```mermaid
flowchart TD
    A[User Message] --> B[Session Initialization]
    B --> C[Load Conversation History]
    C --> D[Build Memory Context]
    D --> E[Assemble System Prompt]
    E --> F[Append User Message]
    F --> G{Context Compression<br/>Needed?}
    
    G -->|Yes| H[Compress Context]
    H --> I[Create Child Session]
    I --> J[Rebuild System Prompt]
    J --> K[LLM API Call]
    
    G -->|No| K
    
    K --> L{Has Tool Calls?}
    
    L -->|Yes| M[Process Tool Calls]
    M --> N[Coerce Argument Types]
    N --> O{Agent-Level Tool?}
    
    O -->|Yes memory/todo| P[Intercept in Agent Loop]
    O -->|No| Q[Registry Dispatch]
    
    P --> R[Execute Tool]
    Q --> R
    
    R --> S{Parallel Safe?}
    S -->|Yes| T[ThreadPoolExecutor]
    S -->|No| U[Sequential Execution]
    
    T --> V[Collect Results]
    U --> V
    
    V --> W[Append Tool Results]
    W --> X{Iteration Budget<br/>Remaining?}
    
    X -->|Yes| K
    X -->|No| Y[Return Error: Max Iterations]
    
    L -->|No Content Only| Z[Final Response]
    Z --> AA[Stream to User]
    AA --> AB[Save to SessionDB]
    AB --> AC[Update Token Counts]
    AC --> AD[Calculate Cost]
    AD --> AE[Return Response]
    
    Y --> AF[Cleanup Resources]
    AE --> AF
```

## 2. 工具调用执行流程 (Tool Call Execution)

```mermaid
sequenceDiagram
    participant L as LLM
    participant A as AIAgent
    participant M as model_tools.py
    participant R as Registry
    participant T as Tool Handler
    participant D as SessionDB
    
    L->>A: response.tool_calls
    loop For each tool_call
        A->>A: Parse tool name & args
        A->>M: handle_function_call<br/>(name, args, task_id)
        
        M->>M: coerce_tool_args<br/>string→int/bool
        M->>M: Check _AGENT_LOOP_TOOLS
        
        alt Agent-level tool
            M->>A: Return stub error
            A->>A: Execute with state
        else Registry tool
            M->>R: dispatch tool_name
            R->>R: Lookup handler
            R->>T: Call handler args
            T->>T: Execute logic
            T-->>R: Return JSON result
            R-->>M: Return result
        end
        
        M-->>A: Tool result JSON
        A->>D: append_message<br/>role="tool"
    end
    
    A->>L: New API call with<br/>tool results
```

## 3. 会话生命周期 (Session Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> Creating: New message received
    
    Creating --> Active: Session created
    Active --> Active: Conversation turns
    Active --> Compressing: Context threshold reached
    
    Compressing --> Active: Compression complete
    Compressing --> Ended: Compression limit
    
    Active --> Ended: User command /exit
    Active --> Ended: Max iterations
    Active --> Ended: Inactivity timeout
    
    Ended --> Archived: Session persisted
    Archived --> Resumed: User resumes
    
    Resumed --> Active: Load history
    
    note right of Active
        - Append messages
        - Update token counts
        - Track tool calls
    end note
    
    note right of Compressing
        - Summarize middle
        - Protect head/tail
        - Create child session
    end note
```

## 4. 上下文压缩流程 (Context Compression)

```mermaid
flowchart TD
    A[Check Token Count] --> B{Tokens >= Threshold?}
    
    B -->|No| C[Continue Normal]
    B -->|Yes| D[Start Compression]
    
    D --> E[Prune Old Tool Results]
    E --> F[Identify Head Messages<br/>Protect first 3]
    F --> G[Identify Tail Messages<br/>Protect last 20K tokens]
    
    G --> H[Extract Middle Section]
    H --> I{Has Previous Summary?}
    
    I -->|Yes| J[Iterative Update<br/>Merge old + new]
    I -->|No| K[Generate New Summary]
    
    J --> L[Call Summarizer LLM]
    K --> L
    
    L --> M[Structured Template:<br/>Resolved/Pending/Work]
    M --> N[Create Child Session]
    N --> O[Link parent_session_id]
    
    O --> P[Copy System Prompt]
    P --> Q[Append Summary to Messages]
    Q --> R[Continue in Child Session]
    
    R --> S[Update Compression Count]
    S --> T[Return Compressed Messages]
```

## 5. Gateway 消息路由 (Gateway Message Routing)

```mermaid
flowchart TD
    subgraph Platform Adapters
        A1[Telegram]
        A2[Discord]
        A3[Slack]
        A4[WhatsApp]
    end
    
    A1 --> B[MessageEvent]
    A2 --> B
    A3 --> B
    A4 --> B
    
    B --> C[GatewayRunner]
    C --> D[SessionStore]
    
    D --> E{Session Exists?}
    E -->|No| F[Create New Session]
    E -->|Yes| G[Load History]
    
    F --> H[Build Session Context]
    G --> H
    
    H --> I[Generate Session Key]
    I --> J[PII Redaction Optional]
    J --> K[Build System Prompt Section]
    
    K --> L[AIAgent.run_conversation]
    L --> M[Get Response]
    
    M --> N[DeliveryRouter]
    N --> O{Has Home Channel?}
    
    O -->|Yes| P[Route to Home]
    O -->|No| Q[Route to Source]
    
    P --> R[Send Message]
    Q --> R
    
    R --> S[Save to SessionDB]
```

## 6. 工具注册与发现 (Tool Registry & Discovery)

```mermaid
flowchart TD
    A[Module Import] --> B[_discover_tools]
    
    B --> C1[Import web_tools]
    B --> C2[Import terminal_tool]
    B --> C3[Import file_tools]
    B --> C4[Import browser_tool]
    
    C1 --> D[registry.register]
    C2 --> D
    C3 --> D
    C4 --> D
    
    D --> E[Store in Registry]
    
    E --> F[get_tool_definitions]
    F --> G{Filter by Toolset}
    
    G -->|enabled_toolsets| H[Include specified]
    G -->|disabled_toolsets| I[Exclude specified]
    G -->|none| J[Include all available]
    
    H --> K[Check Requirements]
    I --> K
    J --> K
    
    K --> L{Env vars present?}
    L -->|Yes| M[Include Tool]
    L -->|No| N[Skip Tool]
    
    M --> O[Return Schema List]
    N --> O
```

## 7. 内存管理系统 (Memory Management)

```mermaid
flowchart TD
    A[User Message] --> B{Memory Context<br/>Needed?}
    
    B -->|Yes| C[MemoryStore.load]
    B -->|No| D[Skip Memory]
    
    C --> E[Query Recent Memories]
    E --> F[Build Context Block]
    F --> G[Inject to System Prompt]
    
    G --> H[LLM Processing]
    H --> I{Save to Memory?}
    
    I -->|Yes| J[memory tool call]
    J --> K[MemoryStore.save]
    K --> L[SQLite Insert]
    L --> M[Update Index]
    
    I -->|No| N[Continue]
    
    M --> N
    D --> N
```

## 8. 技能系统工作流 (Skills System Workflow)

```mermaid
flowchart TD
    A[Complex Task Complete<br/>5+ tool calls] --> B[Trigger Skill Creation]
    
    B --> C[Extract Workflow]
    C --> D[Generate YAML Index]
    D --> E[Save Prompts]
    
    E --> F[Write to ~/.hermes/skills/]
    F --> G[Update Skill Registry]
    
    G --> H[Skill Available Next Time]
    
    H --> I[User References Skill]
    I --> J[skill_view tool]
    J --> K[Load Prompts]
    K --> L[Inject to Context]
    
    L --> M[Execute Skill Workflow]
    
    style A fill:#f9f,stroke:#333
    style H fill:#9f9,stroke:#333
    style M fill:#ff9,stroke:#333
```

## 9. 并行工具执行 (Parallel Tool Execution)

```mermaid
flowchart TD
    A[Multiple Tool Calls] --> B{Check Parallel Safety}
    
    B --> C1{Contains<br/>_NEVER_PARALLEL_TOOLS?}
    C1 -->|Yes clarify/terminal| D[Sequential Execution]
    
    C1 -->|No| C2{All tools in<br/>_PARALLEL_SAFE_TOOLS?}
    C2 -->|Yes| C3{Path overlap?<br/>for file tools}
    
    C3 -->|Yes overlap| D
    C3 -->|No overlap| E[Parallel Execution]
    C2 -->|No mixed| D
    
    D --> F[Execute tool_1]
    F --> G[Wait result_1]
    G --> H[Execute tool_2]
    H --> I[Wait result_2]
    I --> J[Collect all results]
    
    E --> K1[Submit tool_1 to pool]
    E --> K2[Submit tool_2 to pool]
    E --> K3[Submit tool_3 to pool]
    
    K1 --> L[ThreadPoolExecutor<br/>max_workers=8]
    K2 --> L
    K3 --> L
    
    L --> M[Concurrent Execution]
    M --> N[Collect all results]
    
    J --> O[Append to messages]
    N --> O
```

## 10. 配置加载流程 (Configuration Loading)

```mermaid
flowchart TD
    A[Agent Startup] --> B[Load .env Files]
    
    B --> C1[~/.hermes/.env]
    B --> C2[./.env project]
    
    C1 --> D[Set Environment Vars]
    C2 --> D
    
    D --> E{Config File Exists?}
    
    E -->|Yes ~/.hermes/config.yaml| F[Load User Config]
    E -->|Yes ./cli-config.yaml| G[Load Project Config]
    E -->|No| H[Use Defaults]
    
    F --> I[Merge with Defaults]
    G --> I
    H --> I
    
    I --> J[Apply Environment Overrides]
    J --> K[Validate Config]
    
    K --> L{Config Warnings?}
    L -->|Yes| M[Log Warnings]
    L -->|No| N[Config Ready]
    
    M --> N
    
    N --> O[Initialize Components]
    O --> P[Load Skin Theme]
    P --> Q[Discover Tools]
    Q --> R[Ready for Input]
```

## 11. 错误处理与恢复 (Error Handling & Recovery)

```mermaid
flowchart TD
    A[LLM API Call] --> B{Success?}
    
    B -->|Yes| C[Process Response]
    
    B -->|No| D{Error Type}
    
    D -->|Context Length| E[Parse Context Limit]
    E --> F[Update Model Metadata]
    F --> G[Trigger Compression]
    G --> A
    
    D -->|Rate Limit| H[Jittered Backoff]
    H --> I[Retry with Delay]
    I --> A
    
    D -->|Auth Error| J[Check API Key]
    J --> K{Key Configured?}
    K -->|No| L[Return Auth Error]
    K -->|Yes| I
    
    D -->|Tool Error| M[Capture Error Message]
    M --> N[Return as Tool Result]
    N --> O[LLM Sees Error]
    O --> P[LLM May Retry]
    P --> A
    
    D -->|Network| Q[Retry 3x]
    Q --> R{Retries Exhausted?}
    R -->|No| I
    R -->|Yes| S[Return Network Error]
    
    C --> T[Success Path]
    S --> U[Error Path]
```

## 12. 多 Agent 委派 (Multi-Agent Delegation)

```mermaid
flowchart TD
    A[Parent Agent] --> B{delegate_task Tool}
    
    B -->|Called| C[Create Subagent]
    C --> D[Copy Toolset]
    D --> E[Set Max Iterations<br/>delegation.max_iterations]
    
    E --> F[Subagent.run_conversation]
    F --> G[Subagent Tool Calls]
    
    G --> H{Tool in<br/>_AGENT_LOOP_TOOLS?}
    H -->|Yes memory/todo| I[Return Stub Error]
    H -->|No| J[Execute Normally]
    
    I --> K[Subagent Continues]
    J --> K
    
    K --> L{Subagent Done?}
    L -->|No| G
    L -->|Yes| M[Collect Final Response]
    
    M --> N[Return to Parent]
    N --> O[Parent Continues]
    
    O --> P{Parent Budget<br/>Remaining?}
    P -->|Yes| Q[More Tool Calls]
    P -->|No| R[Return Final]
    
    Q --> G
```

## 13. 会话搜索与召回 (Session Search & Recall)

```mermaid
flowchart TD
    A[User References Past] --> B[session_search Tool]
    
    B --> C[Parse Query]
    C --> D[FTS5 Search]
    
    D --> E[Query messages_fts]
    E --> F[MATCH query]
    
    F --> G{Source Filter?}
    G -->|Yes| H[Filter by source]
    G -->|No| I[All Sources]
    
    H --> J[Role Filter?]
    I --> J
    
    J -->|Yes| K[Filter user/assistant/tool]
    J -->|No| L[All Roles]
    
    K --> M[Get Matches]
    L --> M
    
    M --> N[Add Context<br/>±1 message]
    N --> O[Generate Snippets]
    
    O --> P[Return Results]
    P --> Q[Append to Messages]
    Q --> R[LLM Uses Context]
```

## 14. 令牌跟踪与计费 (Token Tracking & Billing)

```mermaid
flowchart TD
    A[LLM API Response] --> B[Extract Usage]
    
    B --> C1[prompt_tokens]
    B --> C2[completion_tokens]
    B --> C3[cache_read_tokens]
    B --> C4[cache_write_tokens]
    B --> C5[reasoning_tokens]
    
    C1 --> D[Update Session]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    
    D --> E[SessionDB.update_token_counts]
    E --> F[Increment Counters]
    
    F --> G[Calculate Cost]
    G --> H[Lookup Pricing]
    H --> I[Apply Rates]
    
    I --> J[estimated_cost_usd]
    J --> K[Update Session]
    
    K --> L{Actual Cost<br/>Available?}
    L -->|Yes OpenRouter| M[actual_cost_usd]
    L -->|No| N[Use Estimate]
    
    M --> O[Final Cost Record]
    N --> O
```

## 15. 皮肤/主题引擎 (Skin/Theme Engine)

```mermaid
flowchart TD
    A[CLI Startup] --> B[Load display.skin Config]
    
    B --> C{Skin Name}
    C -->|default| D[Load Built-in]
    C -->|ares/mono/slate| D
    C -->|custom| E[Load ~/.hermes/skins/]
    
    D --> F[SkinConfig Object]
    E --> F
    
    F --> G[Initialize Components]
    
    G --> H1[Banner Colors]
    G --> H2[Spinner Faces]
    G --> H3[Tool Prefix]
    G --> H4[Response Box]
    
    H1 --> I[Render Banner]
    H2 --> J[Animate Spinner]
    H3 --> K[Format Tool Output]
    H4 --> L[Display Response]
    
    I --> M[Unified Theme]
    J --> M
    K --> M
    L --> M
```

---

## 图例说明 (Legend)

### 流程图符号
- **矩形**: 处理步骤
- **菱形**: 决策点
- **圆角矩形**: 开始/结束
- **平行四边形**: 输入/输出

### 状态图符号
- **实心圆**: 初始状态
- **双环圆**: 结束状态
- **圆角矩形**: 状态
- **箭头**: 状态转换

### 序列图符号
- **垂直线**: 生命线
- **实线箭头**: 调用
- **虚线箭头**: 返回
- **激活框**: 执行中
