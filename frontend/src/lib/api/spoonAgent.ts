/**
 * SpoonOS React Agent / Graph Agent 集成
 * 严格按照 README 要求：必须使用 React Agent 或 Graph Agent 作为核心功能模块
 * 
 * 参考文档：
 * - SpoonOS 技术文档：https://docs.google.com/document/d/1v9tdC_0CABmgsfznJQa_qkWxyYcgW3e5RI9n5gkAEWk/edit?usp=sharing
 * - SpoonOS SDK：https://xspoonai.github.io/docs/getting-started/installation/
 */

interface AgentConfig {
  apiKey: string;
  baseUrl?: string;
}

interface AgentTask {
  type: "reflection" | "analysis" | "suggestion";
  input: string;
  context?: Record<string, any>;
}

interface AgentResponse {
  result: string;
  metadata?: Record<string, any>;
}

/**
 * SpoonOS React Agent 实现
 * React Agent 是一个可以自主思考、规划、执行的 AI Agent
 * 它会进行多轮思考迭代，最终输出结构化的结果
 */
export class SpoonOSReactAgent {
  private apiKey: string;
  private baseUrl: string;

  constructor(config: AgentConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || "https://api.spoonos.ai";
  }

  /**
   * 执行 React Agent 任务
   * React Agent 的核心特点：
   * 1. 自主思考：Agent 会分析任务，制定计划
   * 2. 迭代执行：通过多轮思考优化结果
   * 3. 结构化输出：返回思考过程和最终结果
   */
  async execute(task: AgentTask): Promise<AgentResponse> {
    try {
      // SpoonOS React Agent API 调用
      // 根据官方文档，React Agent 使用特定的端点
      const response = await fetch(`${this.baseUrl}/v1/agent/react`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          task: task.type,
          input: task.input,
          context: task.context || {},
          // React Agent 特定参数
          max_iterations: 3, // 最大思考迭代次数
          temperature: 0.7,
          enable_reasoning: true, // 启用推理过程
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("React Agent API error:", errorText);
        throw new Error(`React Agent API error: ${response.status}`);
      }

      const data = await response.json();
      
      // React Agent 返回结构化的思考过程和结果
      return {
        result: data.result || data.output || "",
        metadata: {
          iterations: data.iterations || [],
          reasoning: data.reasoning || [],
          actions: data.actions || [],
          final_thought: data.final_thought,
        },
      };
    } catch (error: any) {
      console.error("React Agent error:", error);
      throw error;
    }
  }

  /**
   * 心理辅导专用的 React Agent 方法
   * Agent 会自主思考用户的情感状态，生成个性化的反馈
   */
  async generateReflection(
    userText: string,
    taskInfo: { dayIndex: number; title: string; instruction: string }
  ): Promise<{ note: string; next: string }> {
    const task: AgentTask = {
      type: "reflection",
      input: userText,
      context: {
        dayIndex: taskInfo.dayIndex,
        taskTitle: taskInfo.title,
        taskInstruction: taskInfo.instruction,
        role: "心理辅导AI助手",
        style: "温暖、治愈、简单、不评判",
        outputFormat: {
          note: "今日感悟，50字以内，理解用户的感受",
          next: "下一步建议，30字以内，具体可执行",
        },
      },
    };

    const response = await this.execute(task);
    const result = response.result;

    // 解析 React Agent 的响应
    // Agent 会返回结构化的思考结果
    let note = "";
    let next = "";

    // 优先使用 Agent 的结构化输出
    if (response.metadata?.final_thought) {
      const structured = response.metadata.final_thought;
      if (typeof structured === "object") {
        note = structured.note || structured.understanding || structured.感悟 || "";
        next = structured.next || structured.suggestion || structured.建议 || "";
      }
    }

    // 如果没有结构化输出，解析文本响应
    if (!note || !next) {
      const lines = result.split("\n").filter((l: string) => l.trim());
      
      // 查找包含"感悟"或"理解"的行
      const noteLine = lines.find((l: string) => 
        l.includes("感悟") || l.includes("理解") || l.includes("note") || l.includes("Note")
      );
      note = noteLine?.replace(/^[^\u4e00-\u9fa5]*/, "").slice(0, 50) || 
             lines[0]?.slice(0, 50) || "今天你把这件事写出来了，这是很好的开始。";
      
      // 查找包含"下一步"或"建议"的行
      const nextLine = lines.find((l: string) => 
        l.includes("下一步") || l.includes("建议") || l.includes("next") || l.includes("Next")
      );
      next = nextLine?.replace(/^[^\u4e00-\u9fa5]*/, "").slice(0, 30) || 
             lines[1]?.slice(0, 30) || "继续记录你的感受吧。";
    }

    return {
      note: note.slice(0, 50),
      next: next.slice(0, 30),
    };
  }
}

/**
 * SpoonOS Graph Agent 实现
 * Graph Agent 使用工作流图来组织任务，适合复杂的多步骤处理
 */
export class SpoonOSGraphAgent {
  private apiKey: string;
  private baseUrl: string;

  constructor(config: AgentConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || "https://api.spoonos.ai";
  }

  /**
   * 执行 Graph Agent 任务
   * Graph Agent 的核心特点：
   * 1. 工作流图：通过节点和边定义处理流程
   * 2. 并行处理：可以并行执行多个节点
   * 3. 数据流转：节点之间通过边传递数据
   */
  async execute(graph: {
    nodes: Array<{ id: string; type: string; config: any }>;
    edges: Array<{ from: string; to: string }>;
    input: string;
  }): Promise<AgentResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/v1/agent/graph`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          graph: {
            nodes: graph.nodes,
            edges: graph.edges,
          },
          input: graph.input,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Graph Agent API error:", errorText);
        throw new Error(`Graph Agent API error: ${response.status}`);
      }

      const data = await response.json();
      
      return {
        result: data.result || data.output || "",
        metadata: {
          execution_path: data.execution_path || [],
          node_results: data.node_results || {},
        },
      };
    } catch (error: any) {
      console.error("Graph Agent error:", error);
      throw error;
    }
  }

  /**
   * 心理辅导专用的 Graph Agent 工作流
   * 定义：理解 -> 分析 -> 生成反馈 的工作流
   */
  async generateReflection(
    userText: string,
    taskInfo: { dayIndex: number; title: string; instruction: string }
  ): Promise<{ note: string; next: string }> {
    // 定义工作流图：理解 -> 分析 -> 生成反馈
    const graph = {
      nodes: [
        {
          id: "understand",
          type: "llm",
          config: {
            prompt: `理解用户的感受和想法。用户输入：${userText}`,
            role: "心理辅导助手",
            temperature: 0.7,
          },
        },
        {
          id: "analyze",
          type: "llm",
          config: {
            prompt: "分析用户的情感状态、需求和成长点",
            temperature: 0.7,
          },
        },
        {
          id: "generate",
          type: "llm",
          config: {
            prompt: `生成温暖、治愈的反馈。要求：
- note（今日感悟）：50字以内，理解用户的感受，用温暖的语言回应
- next（下一步）：30字以内，给出一个具体、可执行的小建议
风格：温馨、治愈、简单`,
            temperature: 0.7,
          },
        },
      ],
      edges: [
        { from: "understand", to: "analyze" },
        { from: "analyze", to: "generate" },
      ],
      input: userText,
    };

    const response = await this.execute(graph);
    const result = response.result;

    // 解析结果
    let note = "";
    let next = "";

    // 优先使用节点结果
    if (response.metadata?.node_results) {
      const generateResult = response.metadata.node_results["generate"];
      if (generateResult) {
        const parsed = this.parseReflection(generateResult.output || generateResult);
        note = parsed.note;
        next = parsed.next;
      }
    } else {
      const parsed = this.parseReflection(result);
      note = parsed.note;
      next = parsed.next;
    }

    return {
      note: note.slice(0, 50),
      next: next.slice(0, 30),
    };
  }

  private parseReflection(text: string): { note: string; next: string } {
    const lines = text.split("\n").filter((l: string) => l.trim());
    const note = lines.find((l: string) => l.includes("感悟") || l.includes("理解") || l.includes("note"))?.replace(/^[^\u4e00-\u9fa5]*/, "").slice(0, 50) || 
                 lines[0]?.slice(0, 50) || "今天你把这件事写出来了，这是很好的开始。";
    const next = lines.find((l: string) => l.includes("下一步") || l.includes("建议") || l.includes("next"))?.replace(/^[^\u4e00-\u9fa5]*/, "").slice(0, 30) || 
                 lines[1]?.slice(0, 30) || "继续记录你的感受吧。";
    return { note, next };
  }
}

/**
 * 根据配置选择使用 React Agent 或 Graph Agent
 * 默认使用 React Agent（更灵活，适合心理辅导场景）
 */
export function createSpoonOSAgent(config: AgentConfig, agentType: "react" | "graph" = "react") {
  if (agentType === "react") {
    return new SpoonOSReactAgent(config);
  } else {
    return new SpoonOSGraphAgent(config);
  }
}
