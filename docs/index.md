<style>
  .grid.cards li:hover {
    background-color: #ffc929;
  }
[data-md-color-scheme="slate"] .grid.cards li:hover {
    background-color: #673ab6;
  }
</style>

<div align="center" style="text-align:center; background:none; margin: 0 auto;">
  <img src="images/ExperimentsEngine-DarkBG.svg#only-dark" alt="ExE logo dark mode" width="100%" style="max-width: 100%; height: auto;" />
  <img src="images/ExperimentsEngine-White.svg#only-light" alt="ExE logo light mode" width="100%" style="max-width: 100%; height: auto;" />
</div>

## What is the Experiments Engine?

Experiments Engine (ExE) enables social sector orgs with digital offerings to create and monitor experiments.
<figure class="video_container">
    <video controls="true" allowfullscreen="true">
        <source src="./images/ExE_mab_recording.mp4" type="video/mp4">
    </video>
</figure>

## How does it work?

### Creating an experiment

You can create a new experiment in ExE and generate an API key. There are two places where you need to integrate ExE:
(a) when a user visits your platform and you need to decide which arm to assign to them
(b) when the desired outcome is observed (e.g. user clicks a button, user completes a task, etc.)


``` mermaid
sequenceDiagram
    autonumber
    actor Admin
    Admin->>ExE: Create experiment
    Admin->>ExE: Generate API key
    ExE-->>Admin: API key
    Admin->>Your app: Integrate endpoint with platform
```

### Running the experiment

With integration complete, you are ready to run the experiment. When a user visits your platform, your app will call the ExE API to get the arm assigned to them. You can then show them the content for that arm.

When the outcome is observed your platform, the platform will send the outcome data back to ExE. ExE will then update the weights and results of the experiment.

```mermaid
sequenceDiagram
    autonumber
    actor User
    User->>Your app: Visit platform
    Your app->>ExE: Get arm assignment
    ExE->>Your app: Assign an arm to user
    Your app->>User: Show arm content
    User->>Your app: Interact with platform
    Your app->>ExE: Send outcome data
    ExE->>ExE: Update weights and results
    actor Admin
    Admin->>ExE: Monitor experiment
```

See [Setup your first experiment](./first-experiment/index.md) for a step-by-step guide.

### Features

<div class="grid cards" markdown >
- :fontawesome-solid-lightbulb: Intuitive UI to __create and monitor experiments__
- :material-view-dashboard: __Dashboard__ to monitor all your experiments in one place
- :material-message-check: Get __notified when events__ (e.g. number of trials run, number of days passed, etc.) occur
- :fontawesome-solid-magnifying-glass: __Track users__ across experiments and arms
- :fontawesome-solid-gears: __Multiple methods__: A/B testing, multi-armed bandit, and more
</div>

Want other features not listed here? Raise an issue in our [GitHub repository](https://github.com/IDinsight/experiments-engine) or reach out to us at [dsem@idinsight.org](mailto:dsem@idinsight.org)

## Why ExE?

As penetration of smart phones and internet has increased in the Global South, there has been a surge in the number of digital offerings by social sector organizations.

Platform owners have numerous ideas on how to improve user experience and increase engagement but are hampered by the lack of technical expertise and resources to test these ideas.

We are building ExE to reduce these barriers to experimentation. We want to make it easy for platform owners to test out their ideas and make data-driven decisions. Our goal is to help orgs iterate, learn, and improve their offerings at low cost.

## What is it not?

To measure the impact of your offering as a whole, you may need to do an impact evaluation. This tool does not replace that. Instead, it allows your to tweak nodes in your theory of change.

If you are looking for unbiased estimates of average treatment effects (say you want to publish an academic paper) this tool is not for you. Instead, this tool is for platform owners who want to quickly learn what works and what doesn't.

## Who is it for?

ExE is for social sector orgs - NGOs, social enterprises, and developing country governments - who have digital offerings and a keen desire to improve them.

## What kind of ideas can I test out?

Any idea where can both implement and measure the outcome digitally can be tested out using ExE.

Here are some ideas our partners are interested in testing out:

- [x] Does the personalised AI response lead to better user engagement?
- [x] Does using a casual tone with younger users lead to higher completion rates?
- [x] Does reducing the number of questions asked during onboarding lead to lower drop-off rates?
- [x] What is the best time to send messages to ensure users engage with it?
- [x] Will this new feature lead to greater time spent on the platform?

## Design principles

Here are the principles that guide the design of ExE:

- **Simple**: You don't need to be statistician or engineer to use ExE. It is designed for non-technical platform owners to create and monitor experiments.
- **Light-weight**: ExE is designed to be light-weight. We want to make it cheap for organizations to use.
- **Minimal data collection**: ExE should store minimal data about users.
- **Open-source**: ExE is open-source. We want to make it easy for organizations to use and contribute to the tool.

## Who are we?

ExE is built by a team of data scientists, engineers, and statisticians at IDinsight. IDinsight's mission is to amplify the impact of our partners by using data and evidence to inform decisions.
