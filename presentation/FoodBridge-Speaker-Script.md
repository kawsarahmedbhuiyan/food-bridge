# FoodBridge — Video Presentation Script

**Deck:** `FoodBridge-CREATE-a-Thon-Deck.pptx` (7 slides)  
**Suggested total runtime:** 6–8 minutes  
**Pace:** ~45–75 seconds per slide  

Use this script while advancing slides in PowerPoint, Keynote, or the generated video.  
`[SLIDE N]` marks when to show slide N. `[PAUSE]` marks a brief beat.

---

## Slide 1 — Title · FoodBridge  
**Target time: 0:00 – 0:45**

`[SLIDE 1]`

> Good [morning/afternoon]. We're presenting **FoodBridge** — an agentic AI system for food waste redistribution.
>
> Every day in Toronto, restaurants and grocers throw away food that is still safe to eat — while shelters and community kitchens struggle to keep up with demand.
>
> FoodBridge connects surplus food to communities in need — **safely, fairly, and transparently**.
>
> This is our CREATE-a-Thon proof of concept: a multi-agent pipeline built on real Toronto and Canada open datasets.

`[PAUSE]` — let the title slide sit for two seconds before advancing.

---

## Slide 2 — The Problem  
**Target time: 0:45 – 2:00**

`[SLIDE 2]`

> The core problem is simple but urgent: **food waste and hunger coexist in the same city**.
>
> Restaurants and grocers discard edible surplus every day. Shelters and community kitchens lack a reliable supply. And today, there is no coordinator that links donors, community need, safety standards, and logistics in one place.
>
> Four groups are impacted:
>
> — **Restaurants and grocers**, who want to donate but need clarity on safety and liability.  
> — **Community kitchens**, who need predictable deliveries.  
> — **Volunteer drivers**, who need a clear route instead of last-minute phone calls.  
> — **Cities and NGOs**, who need oversight and measurable impact.
>
> Today the chain looks like this: surplus food… question mark… hungry communities.
>
> **FoodBridge replaces that question mark** with a pipeline of specialized AI agents. Each agent uses real data — Dinesafe inspections, Biomass waste grids, and food-security signals — to produce a plan that a human coordinator can review and approve.

---

## Slide 3 — Ethical Considerations  
**Target time: 2:00 – 3:15**

`[SLIDE 3]`

> Agentic AI in a social domain must be ethical by design — not as an afterthought. FoodBridge addresses six ethical dimensions directly.
>
> **Safety:** We only accept donors with a current Dinesafe **Pass** rating, and we exclude any establishment with a history of **crucial** health infractions.
>
> **Fairness:** Small community organizations are **prioritized** in matching, and we cap how many pickups go to large chain donors.
>
> **Transparency:** Every agent logs its decisions step by step — the rule applied, the data used, and the outcome. Nothing is hidden.
>
> **Privacy:** We use **aggregate** need data only. We do not track individuals.
>
> **Accountability:** An Ethics Guardian agent performs a final audit, and **human approval is required** before any pickup is dispatched.
>
> **Bias mitigation:** Matching uses **rule-based, auditable scoring** — not a black-box model — so coordinators can explain every pairing.

`[PAUSE]`

---

## Slide 4 — Proof of Concept  
**Target time: 3:15 – 4:45**

`[SLIDE 4]`

> Here is how the proof of concept works: **six specialized agents** fed by **four real datasets**.
>
> The **datasets:**
> — **Dinesafe** gives us safe donors and GPS coordinates.  
> — **Biomass Canada** maps organic waste hotspots — a proxy for where surplus pressure is high.  
> — **GDELT** provides food-security news events — where hunger signals are rising.  
> — **Supply chain data** adds context when disruptions may create extra unsold inventory.
>
> The **agent pipeline** runs in order:
>
> One — the **Surplus Estimator** scores where surplus food is likely.  
> Two — the **Need Prioritizer** ranks which neighborhoods need food most urgently.  
> Three — the **Donor Scout** filters to ethics-approved, Pass-only establishments.  
> Four — the **Matcher** pairs donors with kitchens by distance, need, and fairness rules.  
> Five — the **Logistics Planner** builds an optimized pickup route.  
> Six — the **Ethics Guardian** audits the full plan and flags anything requiring human review.
>
> Data flows left to right: waste and need signals in… safe matches and a route out… with a human sign-off at the end.

`[Optional note if asked about live system]`  
> Our deployed PoC also includes a seventh **Timing Negotiator** agent that schedules evening pickup windows — you'll see that in the demo.

---

## Slide 5 — Live Demo  
**Target time: 4:45 – 5:45**

`[SLIDE 5]`

> FoodBridge ships as both a **command-line tool** and a **web dashboard**.
>
> From the terminal, a coordinator runs:
> *python main.py --region Scarborough --top 3*
>
> That executes the full agent pipeline and prints the priority zone, top matches, pickup route, and ethics report.
>
> The web app runs on FastAPI. Open the dashboard, pick a region, set how many matches you want, and click **Run planning**.
>
> You get an **interactive map** of the route, an **agent pipeline view**, match cards with scores and distances, and an **ethics panel** showing fairness and safety notes.
>
> Here is an example match from a real run: **Al-Mina Halal Grocery** matched to **Downtown Emergency Kitchen** — score zero-point-eight-one, six-point-four kilometres, Dinesafe Pass, ethics approved — **awaiting human dispatch**.

`[If doing live demo]`  
> Let me show that now… *(switch to browser or terminal)*

`[If not live]`  
> `[PAUSE]` — advance after describing the UI.

---

## Slide 6 — Scalability  
**Target time: 5:45 – 6:45**

`[SLIDE 6]`

> Scalability is built into the architecture.
>
> **Today — proof of concept:** Toronto Dinesafe and Biomass data, a six-agent orchestrator, CLI and web dashboard. Enough to prove the concept end to end.
>
> **Next — pilot:** Partner with two or three community kitchens, add real-time donor SMS alerts, and a simple volunteer driver app.
>
> **Scale — city and industry:** Swap in dataset adapters for other cities, expose an API for NGOs and grocers, and report municipal waste-reduction KPIs.
>
> Agents are **modular** — the same pipeline works in another city by changing the data source, not rewriting the logic. HuggingFace pipelines can refresh need signals daily.
>
> This fits naturally into **public-sector food security programs** and **waste diversion targets**.

---

## Slide 7 — Closing  
**Target time: 6:45 – 7:30**

`[SLIDE 7]`

> To close: FoodBridge brings four data sources together into one fair, auditable plan.
>
> **Biomass** finds waste hotspots.  
> **GDELT** finds hunger hotspots.  
> **Dinesafe** finds safe donors.  
> And our **agents** build a pickup plan that puts people first.
>
> Surplus food no longer stops at a question mark — it reaches the communities that need it most.
>
> Thank you. We're happy to take your questions.

`[SLIDE 7 — hold]`  
> `[PAUSE 3 seconds]` — smile, open for Q&A.

---

## Q&A — Quick reference

| Question | Suggested answer |
|----------|------------------|
| *Is the food actually safe?* | Only Dinesafe Pass donors; crucial infractions excluded; human approval before dispatch. |
| *Why agents instead of one AI?* | Separate concerns (ethics, routing, matching); each step is auditable and swappable. |
| *How is this different from Second Harvest?* | We automate *planning* from open data — a decision-support layer coordinators still approve. |
| *Can this work outside Toronto?* | Yes — swap Dinesafe for any city's inspection data; Biomass grids cover Canada. |
| *What data do you use?* | Dinesafe, Biomass MSW, GDELT food security, optional supply-chain signals. |

---

## Recording checklist

- [ ] Open `FoodBridge-CREATE-a-Thon-Deck.pptx` in full-screen slide show  
- [ ] Use this script as teleprompter or memorize section per slide  
- [ ] Optional: play pre-generated audio from `presentation/audio/` (see `scripts/build_presentation_video.py`)  
- [ ] Record screen + microphone (QuickTime, OBS, or PowerPoint “Record Slide Show”)  
- [ ] Target length: **under 8 minutes** for CREATE-a-Thon judging  
