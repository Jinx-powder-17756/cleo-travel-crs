import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from src.config import get_api_key, get_gemini_client, DEFAULT_MODEL
from src.schemas import UserSession
from src.dataset import EgyptianLandmarksDataset
from src.agent import EgyptianTravelAgent

console = Console()


def display_welcome_banner(dataset_count: int, model_name: str, has_api_key: bool):
    """Renders the startup header."""
    status_badge = "[bold green]ONLINE (Gemini API)[/bold green]" if has_api_key else "[bold yellow]OFFLINE SIMULATION (Set GEMINI_API_KEY to activate Gemini)[/bold yellow]"
    banner_text = (
        f"[bold gold1]🏺 CLEO: Egyptian Travel Assistant & Conversational Recommender[/bold gold1]\n"
        f"[dim]Dynamic Preference Extraction • Stateful Session Memory • Explainable RAG Recommendations[/dim]\n\n"
        f"• Status: {status_badge}\n"
        f"• Model: [cyan]{model_name}[/cyan] | Catalog: [bold cyan]{dataset_count}[/bold cyan] Egyptian Landmarks Loaded\n"
        f"• Commands: [green]/profile[/green] (view state), [green]/dataset[/green] (browse landmarks), [green]/key[/green] (set API key), [green]/reset[/green] (new session), [green]/quit[/green]"
    )
    console.print(Panel(banner_text, border_style="gold1", expand=False))


def display_profile(session: UserSession):
    """Displays the active session state."""
    table = Table(title="🧭 Active Traveler Profile State", border_style="blue", show_header=True)
    table.add_column("Attribute", style="bold cyan", width=22)
    table.add_column("Current Value", style="white")

    profile = session.to_dict()
    interests = profile.get("interests", [])

    table.add_row("User ID", session.user_id)
    table.add_row("Conversation Turns", str(len(session.chat_history) // 2))
    table.add_row("Target City", profile.get("target_city") or "[italic dim]Flexible / Unspecified[/italic dim]")
    table.add_row(
        "Accumulated Interests",
        ", ".join(interests) if interests else "[italic dim]None recorded yet[/italic dim]"
    )
    table.add_row("Travel Style / Vibe", profile.get("budget_or_style") or "[italic dim]Unspecified[/italic dim]")
    table.add_row(
        "Recommended Landmarks",
        ", ".join(session.recommended_landmarks) if session.recommended_landmarks else "[italic dim]None yet[/italic dim]"
    )
    console.print(table)


def display_dataset(dataset: EgyptianLandmarksDataset):
    """Displays landmarks in the catalog."""
    df = dataset.get_all_landmarks()
    table = Table(title="🏛️ Egyptian Landmarks Catalog", border_style="cyan", show_header=True)
    table.add_column("ID", justify="right", style="dim", width=4)
    table.add_column("Landmark", style="bold white", width=26)
    table.add_column("City / Region", style="cyan", width=22)
    table.add_column("Category", style="yellow", width=24)
    table.add_column("Key Highlights & Tags", style="dim", width=35)

    for _, row in df.iterrows():
        table.add_row(
            str(row["id"]),
            str(row["landmark_name"]),
            f"{row['city']} ({row['region']})",
            str(row["category"]),
            str(row["tags"])[:35] + "..."
        )
    console.print(table)


def display_turn_output(agent_resp, extracted):
    """Renders the step-by-step extraction and recommendation output."""
    # Step 1: Extraction Card
    extract_info = (
        f"[bold cyan]New Interests:[/bold cyan] {', '.join(extracted.new_interests) if extracted.new_interests else '[dim]None detected[/dim]'}\n"
        f"[bold cyan]Identified City:[/bold cyan] {extracted.target_city or '[dim]None[/dim]'}\n"
        f"[bold cyan]Travel Style / Vibe:[/bold cyan] {extracted.budget_or_style or '[dim]None[/dim]'}"
    )
    console.print(Panel(extract_info, title="🔍 Step 1: Dynamic Preference Extraction (Pydantic)", border_style="cyan", expand=False))

    # Step 2: Recommendations with Grounded Explanations
    if agent_resp.recommendations:
        console.print("\n[bold gold1]🏛️ Grounded Landmark Recommendations:[/bold gold1]")
        for rec in agent_resp.recommendations:
            content = (
                f"[bold white]{rec.landmark_name}[/bold white] — [cyan]{rec.city}[/cyan] ([yellow]{rec.category}[/yellow])\n"
                f"[bold green]Relevance Score:[/bold green] {rec.match_score:.2f}\n\n"
                f"[bold magenta]Why Matched (Explainability):[/bold magenta]\n{rec.why_matched}\n\n"
                f"[bold yellow]💡 Insider Tip:[/bold yellow] {rec.highlight_tip}"
            )
            console.print(Panel(content, border_style="gold1", expand=False))

    # Step 3: Conversational Response & Follow-up
    reply_content = (
        f"{agent_resp.conversational_reply}\n\n"
        f"[bold cyan]💬 Follow-up:[/bold cyan] {agent_resp.suggested_follow_up}"
    )
    console.print(Panel(reply_content, title="✨ Cleo's Response", border_style="green", expand=False))


def main():
    has_key = bool(get_api_key())
    dataset = EgyptianLandmarksDataset()
    agent = EgyptianTravelAgent(dataset=dataset, model_name=DEFAULT_MODEL)
    session = UserSession(user_id="traveler_01")

    display_welcome_banner(len(dataset.get_all_landmarks()), DEFAULT_MODEL, has_key)

    console.print("\n[italic dim]Try asking something like:[/italic dim]")
    console.print("  [dim]- \"I'm planning a solo trip to Luxor and I love ancient pharaonic temples and hieroglyphics.\"[/dim]")
    console.print("  [dim]- \"We are a family looking for relaxing beaches and diving spots in Sinai.\"[/dim]")
    console.print("  [dim]- \"I want authentic historic markets and delicious street food in Cairo.\"[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold gold1]You[/bold gold1]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Ma'a Salama! Safe travels in Egypt! 🇪🇬[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ["/quit", "exit", "quit", "q"]:
            console.print("[bold gold1]Ma'a Salama! Safe travels in Egypt! 🇪🇬[/bold gold1]")
            break
        elif cmd == "/profile":
            display_profile(session)
            continue
        elif cmd == "/dataset":
            display_dataset(dataset)
            continue
        elif cmd == "/reset":
            session = UserSession(user_id="traveler_01")
            console.print("[bold green]✓ Session memory reset. Ready for a new travel enquiry.[/bold green]\n")
            continue
        elif cmd == "/help":
            console.print("Commands: [green]/profile[/green], [green]/dataset[/green], [green]/key[/green], [green]/reset[/green], [green]/quit[/green]")
            continue
        elif cmd.startswith("/key"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                new_key = parts[1].strip()
            else:
                new_key = Prompt.ask("[cyan]Enter your Gemini API Key[/cyan]").strip()
            if new_key:
                os.environ["GEMINI_API_KEY"] = new_key
                agent = EgyptianTravelAgent(client=get_gemini_client(new_key), dataset=dataset, model_name=DEFAULT_MODEL)
                console.print("[bold green]✓ Gemini API key set and client re-initialized![/bold green]\n")
            continue

        with console.status("[bold gold1]Analyzing query & matching Egyptian landmarks...[/bold gold1]", spinner="dots"):
            extracted = agent.extract_preferences(user_input, session)
            session.update_profile(extracted)
            session.add_message("user", user_input)
            candidates = dataset.retrieve_candidates(session, top_k=3)
            agent_resp = agent.generate_recommendations(user_input, session, candidates, extracted)
            for rec in agent_resp.recommendations:
                session.record_recommendation(rec.landmark_name)
            session.add_message("assistant", agent_resp.conversational_reply)

        display_turn_output(agent_resp, extracted)
        console.print()


if __name__ == "__main__":
    main()
