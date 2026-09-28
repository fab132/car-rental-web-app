# [car-rental-web-app]

**Current stage:** Milestone 1 — design draft. Update this README throughout the project; do not start a separate document for each milestone.

Later sections will be introduced in the fourth theory session and subsequent classes. For now, document the design draft below.

Replace the prompts with your group's current thinking. Drafts and open questions are expected; no running backend, database or complete OpenAPI contract is required for this milestone. If your idea is still undecided, use the bar scenario and class exercises as a starting point and identify what you have adapted.

## Project overview

[Briefly describe the application, its intended users and the problem it addresses.]

### Team and initial responsibilities

| Member | Initial responsibility | Next action |
|---|---|---|
| [Name] | Coordination and README | Keep decisions, questions and the milestone commit together |
| [Name] | Users and workflow | Describe needs and the steps of one workflow |
| [Name] | Sketches and interaction | Sketch the screens and feedback for that workflow |
| [Name] | Data and API exploration | Prepare sample JSON and clarify the proposed operations |

These are suggested starting responsibilities, not permanent silos. Discuss and review each other's work; everyone should understand the draft. Adjust or rotate responsibilities as needed.

## 1. Analysis

### Scenario, users and goals

- Situation or problem: [Who experiences what difficulty?]
- Intended users: [Roles and needs]
- Proposed benefit: [What should improve?]
- Initial scope: [One workflow to explore first; what can wait?]

### User stories and first workflow

Describe the benefit as well as the action: “As a [role], I want to [action], so that [benefit].” For example, serving staff want to record table and item quantities so that the bartender receives a clear order. Identify what is outside the initial scope.

| Step | User / role | Action | Information needed | Expected result or feedback |
|---|---|---|---|---|
| 1 | [Role] | [Action] | [Input] | [Outcome] |

Include a question or exception worth discussing, such as an unavailable menu item. This builds on exercise 1 from the design class.

## 2. Design

### Screens and navigation

Link or embed your sketches for the workflow (paper photos, draw.io or another tool). Explain the main inputs, actions and feedback. This builds on exercise 2. A polished or clickable prototype is not required; add one if you already have it.

### Domain concepts and example data

Link your sample JSON files for relevant things in the workflow. Use fictional data. Explain important fields, value types and references between objects; mark uncertainties. The bar catalogue and order examples are available as a starting point. There is no new fixed entity quota for this draft.

### Business rules and possible operations

Describe a rule and an exception in plain language. Example: order quantities must be positive; discuss what happens when an item is unavailable. Later, explain where the implementation enforces the rule.

| User goal | Proposed action | Example input | Expected output | Open question |
|---|---|---|---|---|
| [Goal] | [Read / create / change / remove something] | [Data needed] | [Result] | [What needs clarification?] |

Use plain language; final endpoints and implementation can follow after coaching. These are draft ideas, not a complete CRUD implementation.

### Inspiration from existing apps or APIs — optional

If useful for your design, link an existing app, website or API and add one or two sentences about what you would adopt or improve for your users. No separate research report or external API integration is required for this milestone.

## 3. Project management

### Decisions, open questions and next steps

| Question / decision | Current position | Next step / person |
|---|---|---|
| [Question] | [Draft answer or undecided] | [Action] |

### Milestone progress

| Milestone | Available evidence | Status / next step |
|---|---|---|
| 1 — Design draft | Analysis, workflow, sketches, example JSON and proposed operations | [Links and open questions] |
| 2 — Contract and available implementation | OpenAPI contract and implemented/tested progress | [Update later] |
| Integration — later | Revised feature scope, frontend decision, architecture and a connected workflow | [Update after classroom examples; details in Moodle] |

Use the Moodle assignment for the complete milestones, dates and assessment criteria. Describe contributions and decisions; commit counts do not measure individual effort.

## 4. References and acknowledgements

List documentation, reused assets, libraries and other assistance relevant to your project, and explain adaptations where appropriate.

Template lineage: the earlier [Pizzeria Reference Project](https://github.com/FHNW-INT/Pizzeria_Reference_Project) organised documentation around analysis, design, implementation, execution and project management. This template updates that structure for the HS26 Python/FastAPI teaching path; its Java/Spring and hosted Budibase setup instructions do not apply here.

## Worked example — adapt, do not submit unchanged

From the design-class workflow and sketch exercises:

- **Need:** serving staff want to record orders without losing items or quantities.
- **Workflow:** select table and items → review quantities → submit → see confirmation. Bar staff can then read the pending order.
- **Sketches:** order form, review/confirmation and pending-orders view. Link your own sketches; paper is sufficient.
- **Data (exercise 1c):** `{"table": 3, "items": [{"menu_item_id": 1, "quantity": 2}]}`. `menu_item_id` refers to an item in the sample catalogue.
- **Proposed operation:** create an order; expected result: an identifier and confirmation. This describes intended behaviour, not an implemented endpoint.
- **API observation:** if you sent the Echo request, record that it repeated the JSON; it did not create an order or enforce quantity rules. If you only read the example, say so.
- **Open question:** how should the app respond when a selected item is unavailable?

For exercise 2, an alternative observation is that weather providers expose different structures, units and time intervals. Record the evidence you actually inspected and why it matters. Your project need not integrate a weather API.

## Friday handoff checklist

- Commit this README and the available draft material before the milestone.
- First join the module's MS Team using the link in Moodle. The lecturer will then add you to your group's private channel during the week.
- Submit the GitHub repository link in Moodle by Friday, following the milestone instructions published after class.
- Ensure the lecturer can access the repository; public visibility is not required.
- If you do not yet have a group channel and your team composition is not recorded in Moodle's team formation activity, email the lecturer with all team members' names. If the composition is already recorded, join the Team so you can be added to the channel. Contact the lecturer if the channel is still unavailable before the deadline.
- Refer to Moodle for the milestone date and the full assignment requirements.

Keep credentials and personal data out of the repository. The draft and its progress are useful evidence for project management; commit counts or lines of code are not measures of individual contribution.
