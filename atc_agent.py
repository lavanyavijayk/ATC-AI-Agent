from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List


# STATE DEFINITION
class AgentState(TypedDict):
    messages: List[dict]
    command: str
    result: str


class ATCAgent:
    def __init__(self, llm):
        self.llm = llm #ChatOpenAI(model=llm)
        self.prune_num = 10
        self.workflow = self.initialization() 
        self.state = {
            "messages": [],
            "command": "",
            "result": ""
        }

    # Limit memory to last N messages
    def prune_messages(self, state: AgentState):
        msgs = state.get("messages", [])
        if len(msgs) > self.prune_num:
            state["messages"] = msgs[-self.prune_num:]
        return state

    # NODE 1 — WAIT FOR COMMAND
    def wait_for_command(self, state: AgentState):
        messages = state["messages"]
        user_msg = messages[-1]["content"]
        state["command"] = user_msg.strip().lower()
        return state

    # NODE 2 — EXECUTE COMMAND
    def execute_command(self, state: AgentState):
        command = state["command"]

        # Stop condition
        if command == "stop":
            state["result"] = "Agent stopped."
            return state

        # Run LLM
        prompt = f"Execute this command: {command}"
        # resp = self.llm.invoke([{"role": "user", "content": prompt}])

        # Update state
        state["result"] = "test"#resp.content
        state["messages"].append(
            {"role": "assistant", "content": "resp.content"}
        )

        return self.prune_messages(state)

    # Routing logic
    def router(self, state: AgentState):
        if state["command"] == "stop":
            return "end"      # MUST MATCH CONDITIONAL EDGES KEYS
        return "wait"

    # Build the graph
    def initialization(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("wait", self.wait_for_command)
        workflow.add_node("execute", self.execute_command)

        workflow.set_entry_point("wait")

        workflow.add_edge("wait", "execute")

        workflow.add_conditional_edges(
            "execute",
            self.router,
            {
                "wait": END,
                "end": END
            }
        )

        # memory = MemorySaver()
        graph = workflow.compile()
        return graph      # return the compiled graph


if __name__ == "__main__":
    # Initialize the agent
    agent = ATCAgent(llm="gpt-4o-mini")

    print("ATC Agent Started. Type a command. Type 'stop' to end.")

    while True:
        # User input
        user_input = input("\nCommand: ")

        # Add user input to agent's internal state
        agent.state["messages"].append({"role": "user", "content": user_input})

        # Run the workflow using the internal state
        result_state = agent.workflow.invoke(
            agent.state
        )


        # Show the agent's output
        print("\nAgent Output:", result_state["result"])

        # Stop if needed
        if result_state.get("command") == "stop":
            print("\nAgent terminated.")
            break

        # Update internal state for next iteration
        agent.state = result_state
