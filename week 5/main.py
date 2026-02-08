import asyncio
from autogen_core import SingleThreadedAgentRuntime, AgentId
from autogen_agentchat.messages import TextMessage
from dotenv import load_dotenv

# Importy Twoich agentów
from dietician import DieticianAgent
from safety_agent import SafetyAgent
from shopping_agent import ShoppingAgent
from inventory_agent import InventoryAgent

load_dotenv()


async def main():
    runtime = SingleThreadedAgentRuntime()

    # Rejestracja agentów
    await DieticianAgent.register(
        runtime, "dietetyk", lambda: DieticianAgent("dietetyk")
    )
    await SafetyAgent.register(
        runtime, "safety", lambda: SafetyAgent(
            "safety", ["mąka pszenna", "cukier biały", "cukier brązowy"])
    )
    await InventoryAgent.register(
        runtime, "inventory", lambda: InventoryAgent(
            "inventory", "Kuchnia_składniki.txt")
    )
    await ShoppingAgent.register(
        runtime, "shopping", lambda: ShoppingAgent("shopping")
    )

    runtime.start()

    # KROK 1: Wczytywanie danych z plików
    with open("Kuchnia_składniki.txt", "r", encoding="utf-8") as f:
        moje_zapasy = f.read()

    with open("Przepisy.txt", "r", encoding="utf-8") as f:
        # Czytamy linki, usuwamy puste linie i robimy ponumerowaną bazę
        linki_raw = [line.strip() for line in f.readlines() if line.strip()]
        # Usuwamy duplikaty, zachowując kolejność
        linki_unikalne = list(dict.fromkeys(linki_raw))
        moje_linki = "\n".join(
            [f"LINK {i+1}: {url}" for i, url in enumerate(linki_unikalne)])

    user_request = f"""
    ZADANIE: Zaplanuj jadłospis na 4 dni.
    Osoba A (52kg, 3 posiłki(śniadanie, obiad, podwieczorek)), Osoba B (75kg, 2 posiłki(obiad, podwieczorek)). 
    Obiad i podwieczorek (ciasto) wspólny dla obu osób. Unikaj koktajli.

    TWOJA BAZA LINKÓW (PAMIĘTAJ KOLEJNOŚĆ):
    {moje_linki}
    
    DOSTĘPNE SKŁADNIKI:
    {moje_zapasy}

    INSTRUKCJE SPECJALNE:
    1. ZAKAZ HALUCYNACJI: Nie wymyślaj własnych linków. 
    2. KOLEJNOŚĆ: Dla obiadu w Dniu 1 użyj adresu opisanego jako LINK 1. Dla Obiadu w Dniu 2 użyj LINK 2, itd.
    3. PODWIECZOREK: Wybierz kolejne wolne linki z listy (np. LINK 5, 6...).
    4. ZERO glutenu i białego cukru (użyj zamienników ze spiżarni).
    5. Podaj link dokładnie w formie: [Nazwa - Przepis z Pinteresta](link_z_listy).
    """

    print("USER: Generuję jadłospis z priorytetem Twoich linków...\n")

    # KROK 2: Dietetyk
    diet_response = await runtime.send_message(
        TextMessage(content=user_request, source="user"),
        AgentId("dietetyk", "default")
    )
    print(f"DIETETYK: Gotowe!\n")

    # KROK 3: Safety
    safety_response = await runtime.send_message(
        TextMessage(content=diet_response.content, source="user"),
        AgentId("safety", "default")
    )

    # KROK 4: Inventory & Shopping
    if safety_response.is_safe:
        inventory_response = await runtime.send_message(
            TextMessage(content=diet_response.content, source="user"),
            AgentId("inventory", "default")
        )

        shopping_response = await runtime.send_message(
            TextMessage(content=inventory_response.content, source="user"),
            AgentId("shopping", "default")
        )

    # KROK 5: Zapis do pliku
    filename = "moj_jadlospis.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write("=== TWÓJ SPERSONALIZOWANY PLAN POSIŁKÓW ===\n\n")
        file.write("--- JADŁOSPIS (4 DNI) ---\n")
        file.write(diet_response.content + "\n\n")

        if safety_response.is_safe:
            file.write("--- DOSTĘPNOŚĆ SKŁADNIKÓW ---\n")
            file.write(inventory_response.content + "\n\n")
            file.write("--- LISTA ZAKUPÓW ---\n")
            file.write(shopping_response.content + "\n")
        else:
            file.write("!!! UWAGA: POSIŁEK NIEBEZPIECZNY !!!\n")
            file.write(f"Powód: {safety_response.reason}\n")
            file.write(f"Sugestia: {safety_response.alternatives}\n")

    print(f"\n[SUKCES] Plan zapisany w: {filename}")
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
