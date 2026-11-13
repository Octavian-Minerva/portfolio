# ALL website copy lives in this one file. Edit text here, then rebuild:
#     .venv/bin/python build_site.py            (warns loudly while any placeholder remains)
#     .venv/bin/python build_site.py --release  (refuses to build while any placeholder remains)
#
# How to fill a placeholder: replace the whole  RyanWrites(...)  call with your text in quotes.
#     PURPOSE = RyanWrites("Purpose statement ...", "30 to 50 words")
# becomes
#     PURPOSE = "I want to ..."
# Long text: separate paragraphs with a blank line inside triple quotes ("""...""").
# Optional items say so; set them to None to remove them from the page.
#
# Rules: Australian English. No em dashes (the build stops if it finds one); en dashes only in ranges.
# Straight quotes and apostrophes are fine: the build turns them into curly ones.


# DRAFTS (13 Nov 2026): Ryan asked the assistant to draft all copy for a feedback preview.
# Every assistant-drafted item is wrapped in Draft(...). It renders normally, but the build counts drafts
# and "--release" refuses to build while any remain. To accept or replace one, swap Draft("...") for
# your own "..." (keep or rewrite the words). The tracker is ../DRAFT-TRACKER.md.

DRAFTS = []

class DraftStr(str):
    pass

class DraftList(list):
    pass

def Draft(x):
    d = DraftList(x) if isinstance(x, list) else DraftStr(x)
    DRAFTS.append(d)
    return d


class RyanWrites:
    """A visible, dashed 'still to write' box. The build counts these and warns until none remain."""
    def __init__(self, what, length='', who='Ryan writes'):
        self.what, self.length, self.who = what, length, who


# ---------------------------------------------------------------- site settings
NAME = "Ryan O'Grady"
SITE_URL = "https://ryanoogrady.netlify.app"            # e.g. "https://ryan-ogrady.netlify.app" once the site has an address (used for link previews)
PAGE_TITLE = "Ryan O'Grady | Bachelor of Arts, Politics, Power and Technology, Swinburne"
META_DESCRIPTION = "Portfolio of Ryan O'Grady, Bachelor of Arts student majoring in Politics, Power and Technology at Swinburne University of Technology."
YEAR = "2026"

NAV = [("About", "about"), ("Work", "work"), ("Skills", "skills"), ("Experience", "experience"), ("Contact", "contact")]

# ---------------------------------------------------------------- 1. hero
HERO_KICKER = "Bachelor of Arts, Politics, Power and Technology, Swinburne University of Technology"
DESCRIPTOR = Draft("Politics student interested in inequality, work, and what automation does to both.")
# Photo: put the file in site-src/img-src/ and set PHOTO = ("your-photo.jpg", "Alt text describing the photo").
# Portrait, 4:5, at least 900 px wide. Until then a neutral monogram shows inside a placeholder box.
PHOTO = ("ryan-portrait.jpg", "Ryan sitting on a rocky summit above a layer of cloud, smiling.")   # cropped from Ryan's photo; location metadata stripped

# ---------------------------------------------------------------- 2. about
ABOUT_HEAD = "About"
PURPOSE = Draft("I want to research how wealth, work and technology shape who gets ahead, so that access to opportunity is not decided by the family you are born into. I am drawn to research because I like hard problems, and I would rather be challenged than stuck in routine.")
ABOUT_BIO = Draft("Since I was eighteen I have worked a string of jobs that taught me more about how work is organised than I expected: a month of street fundraising, three years at a burger chain, swabbing people at COVID testing sites and in hotel quarantine, and nearly four years behind the counter at a self-storage business. Travelling on a budget, including on the cheapest trains in India, did the same for how I see inequality. I came back to study through a diploma in 2025, and those experiences shape most of what I write about.")
INTERESTS_LABEL = "Questions I'm interested in"
INTERESTS = Draft(["How do we stop access to opportunity being decided by the family you are born into?", "Why does rising inequality so often set people against each other, rather than against those accumulating wealth and influence?", "What will the wider rollout of AI do to the labour market, and who will gain from it?"])
EXPLORING_LABEL = "Now, November 2026"
EXPLORING = Draft(["Halfway through my BA, majoring in Politics, Power and Technology", "Moving into infrastructure work on an AI agent platform", "Reading into scientific management and how work is organised"])

# ---------------------------------------------------------------- 3. featured project (also feeds the detail page)
FEATURED = {
    "kicker": "Featured project",
    "title": "Not Our Game",
    "unit_code": "ART20003",
    "unit_name": "Skills and Strategies for Social Change",
    "year": "2026",
    "type": "Group campaign strategy",
    "role": "The campaign website, and the artefacts and messaging sections of the report",
    "live_url": "https://not-our-game.netlify.app",
    "live_label": "Visit the live campaign site",
    "detail_label": "Read about the project",
    "blurb": Draft("Not Our Game is a campaign strategy to prevent domestic and family violence on State of Origin nights, when recorded domestic assaults in New South Wales rise by 40.7%. It asks the NRL and its broadcasters to carry prevention messaging and support-service information during the 2027 Origin broadcasts. I produced the campaign website and wrote the report's messaging and artefact sections."),
    # Screenshots of the campaign site (sources in site-src/img-src/). First two show on the home page.
    "shots": [
        ("campaign-home-desktop.png", "desktop", "Home page, desktop",
         "Home page of the Not Our Game campaign website on a desktop screen, headed 'Love the game. Respect everyone.' over an AI-generated image of four fans watching a game at home, with support phone numbers above."),
        ("campaign-mates-phone.png", "phone", "For mates page, phone",
         "The For mates page on a phone, headed 'Look out for your mates', with a fixed bar of support numbers and a quick exit button along the bottom."),
        ("campaign-request-desktop.png", "desktop", "Our request page, desktop",
         "The Our request page on a desktop screen, headed 'Put family violence support in every Origin broadcast', over a darkened lounge room with a game on the television."),
        ("campaign-help-desktop.png", "desktop", "Get help page, desktop",
         "The Get help page on a desktop screen, headed 'You deserve to be safe', with three large call buttons for support services."),
    ],
}

# Detail page (not-our-game.html). Section headings are labels; the prose is yours.
FEATURED_PAGE = {
    "overview_head": "Overview",
    "overview": Draft("Not Our Game was a group project for ART20003 Skills and Strategies for Social Change. The campaign targets the State of Origin series, when recorded domestic assaults in New South Wales rise by 40.7%. Rather than treating every fan as part of the problem, it speaks to three audiences: the NRL and its broadcasters, who can make the change; fans, particularly men watching in groups; and people experiencing violence, along with those supporting them and men worried about their own behaviour. Its request is simple: prevention messaging and support-service information during the 2027 Origin broadcasts. My part was the campaign website and the report's messaging and artefact sections."),
    "website_head": "The website",
    "website": Draft("The website is the campaign's hub; every social post links back to it, as does the QR code shown with support information during broadcasts. Its pages follow the three audiences. A quick-exit button and support numbers sit on every page, including on mobile, because research on domestic violence websites recommends a clearly labelled exit that stays visible."),
    "messaging_head": "The messaging section",
    "messaging": Draft("The central message, \"Love the Game, Respect Everyone\", keeps the sport and the violence separate, so supporters can reject violence without being cast as critics of the game. Fan-facing material does not lead with assault statistics, because publicising how common a harmful behaviour is can reinforce it. Instead, it offers low-key ways to look out for mates, such as checking in the next day."),
    "tiles_head": "Social posts",
}
# Social tiles you made: (file in site-src/img-src/, alt text, caption). Leave empty to show a placeholder.
SOCIAL_TILES = []
SOCIAL_TILES_TODO = None  # dropped 12 Nov: the campaign tiles were groupmates' work, not Ryan's

# ---------------------------------------------------------------- 4. selected work
# One dict per card. Reorder, delete or add cards freely. Titles are exact titles from the submitted files.
# "pdf": optional (source file in ../essays-src/, public file name); adds a "Read the full essay (PDF)" button.
# "thumb": (file in site-src/img-src/, alt text) shown at the top of the card, cropped to 4:3.
# "links": optional [(label, href, external)] buttons.
# "slides": optional images (file in site-src/img-src/, alt text); a card with slides spans the full width.
WORK_HEAD = "Selected work"
WORK = [
    {
        "title": "Deterring Arrival: Asylum Policy in Australia and the United States",
        "pdf": ("soc20013.pdf", "ryan-ogrady-deterring-arrival-asylum-policy.pdf"),
        "thumb": ("essay-soc20013-p1.png", "First page of the essay, headed Deterring Arrival: Asylum Policy in Australia and the United States."),
        "type": "Major essay",
        "unit_code": "SOC20013", "unit_name": "Race, Ethnicity and Migration", "year": "2026",
        "topic": Draft("How do Australia and the United States keep asylum seekers from reaching the territory where they could claim protection?"),
        "tags": ["Asylum policy", "Migration", "Comparative policy"],
        "blurb": Draft("I argue that both countries have built similar architectures of deterrence on the back of comparable moral panics. Geography explains most differences in form, offshore detention against land buffers. The sharper contrast is durability: Australia's bipartisan consensus against US policy that swings between administrations and the courts."),
    },
    {
        "title": "Insulating News from the Market and the State",
        "pdf": ("his10006.pdf", "ryan-ogrady-insulating-news.pdf"),
        "thumb": ("essay-his10006-p1.png", "First page of the essay, headed Insulating News from the Market and the State."),
        "type": "Major essay",
        "unit_code": "HIS10006", "unit_name": "Propaganda: A History of Media and Politics", "year": "2026",
        "topic": Draft("Should news and information, as public goods, be quarantined from the commercial market, and would that make them independent?"),
        "tags": ["Media policy", "Public goods", "Public broadcasting"],
        "blurb": Draft("I argue that news is only partly a public good, and that quarantine would not make it independent; from the Chicago press in 1918 to Poland in 2021, removing the market simply leaves control with the state. News should instead be insulated from both, through regulatory protection and secure funding."),
    },
    {
        "title": "Footscray: Migrant Settlement and Urban Renewal",
        "thumb_fit": "contain",   # 16:9 slide: show it whole rather than cropping the title
        "thumb": ("footscray-slide-01.png", "Title slide, 'Footscray: Migrant Settlement and Urban Renewal', over a photo of apartment towers beside the river at Footscray."),
        "type": "Tutorial presentation",
        "unit_code": "SOC20013", "unit_name": "Race, Ethnicity and Migration", "year": "2026",
        "topic": Draft("What happens to a gateway suburb for migrants when urban renewal and rising rents arrive?"),
        "tags": ["Migration", "Housing", "Urban renewal", "Melbourne"],
        "blurb": Draft("Footscray has welcomed successive waves of migrants, but state-led renewal and rising rents are pricing out that role, and the gateway is moving west to Brimbank and Wyndham. I recommend public housing that goes beyond essential workers, and long-term leases for the African traders being priced out of their shopfronts."),
    },
    {
        "title": "Three vantage points of the Cold War: Hobsbawm, Gaddis, and Jervis",
        "pdf": ("his10003.pdf", "ryan-ogrady-cold-war-three-vantage-points.pdf"),
        "thumb": ("essay-his10003-p1.png", "First page of the essay, headed Three vantage points of the Cold War: Hobsbawm, Gaddis, and Jervis."),
        "type": "Term essay",
        "unit_code": "HIS10003", "unit_name": "Global History", "year": "2026",
        "topic": Draft("Why do three serious accounts of the Cold War, written before, just after and a decade after the Soviet collapse, disagree?"),
        "tags": ["Cold War", "International relations", "Historiography"],
        "blurb": Draft("I compare Hobsbawm, Gaddis and Jervis and argue that when each wrote, what they could know and the frameworks they used shaped their accounts. They agree on what was observable, split on what drove the rivalry, and converge, by different routes, on the Soviet role in ending it."),
    },
    {
        "title": "Not Our Game",
        "thumb": ("campaign-home-desktop.png", "Home page of the Not Our Game campaign website, headed 'Love the game. Respect everyone.' over an AI-generated image of four fans watching a game at home."),
        "type": "Group campaign strategy",
        "unit_code": "ART20003", "unit_name": "Skills and Strategies for Social Change", "year": "2026",
        "topic": Draft("How can State of Origin broadcasts help prevent domestic and family violence without treating fans as the problem?"),
        "tags": ["Social campaign", "Domestic and family violence", "Messaging"],
        "blurb": FEATURED["blurb"],   # the same Draft as the project page summary
        "links": [("Read about the project", "not-our-game.html", False), ("Visit the live campaign site", "https://not-our-game.netlify.app", True)],
    },
]

# ---------------------------------------------------------------- 5. skills audit and reflection (marked requirement)
SKILLS_HEAD = "Skills and reflection"
SKILLS_KICKER = "What I can do, and where I learnt it"
# Skill areas: each card has a heading, a short paragraph of evidence and a few labels.
SKILL_GROUPS = [
    {
        "title": "Research and argument",
        "text": Draft("Most of my writing compares: three historians on the Cold War, two countries' asylum systems, competing claims about who should fund the news. The biggest change this year came from one piece of tutor feedback, to use sources as evidence, theory or context rather than as authority for a point I had already made. My essays got tighter once the evidence started doing the arguing."),
        "tags": Draft(["Comparative analysis", "Historiography", "Policy analysis", "Academic writing"]),
    },
    {
        "title": "Building systems with AI",
        "text": Draft("I have no formal coding background. What I do have is a habit of breaking a problem into parts and checking each one, which turns out to be most of what directing AI well requires. Since June I have built features for an AI agent platform, including an automated review loop and a single screen for watching every agent at once; before that came Arx, a planner I built for my own study."),
        "tags": Draft(["Systems thinking", "AI-assisted development", "Process design"]),
    },
    {
        "title": "Working with people",
        "text": Draft("Nearly four years at a self-storage business means sales by phone, email and in person, chasing overdue accounts and sorting out whatever goes wrong on site, including covering the assistant manager's shifts while that role was vacant. Earlier jobs added the rest: a month of street fundraising taught me to talk to anyone, and COVID collection in hotel quarantine taught me to work to strict protocol."),
        "tags": Draft(["Customer service", "Difficult conversations", "Working to protocol", "Public speaking"]),
    },
]
REFLECTION_HEAD = "Reflection: the Not Our Game campaign"
SKILLS_AUDIT = Draft("""Not Our Game was my first time planning a social campaign from start to finish, and the part I took most from was the messaging. The obvious move was to open with the statistic that recorded domestic assaults in New South Wales rise by 40.7% on State of Origin nights. The research pointed the other way: publicising how common a harmful behaviour is can make it seem normal, and a campaign that treats every fan as part of the problem loses the audience it most needs. So the fan-facing material leads with something most men already believe, that they are not okay with disrespect, and gives them small ways to act on it.

That decision changed how I think about argument more generally. Being right is not enough if the framing pushes your audience away. Working in a group also meant planning around other people's sections and deadlines, which I will need more of as my work moves towards research. Going forward, I want to keep testing my instincts about framing against the evidence before I commit to them.""")
SKILLS_LIST_LABEL = "Skills"
SKILLS_LIST = None   # replaced by the tags on each skill area (13 Nov)

# ---------------------------------------------------------------- 6. experience and involvement
EXPERIENCE_HEAD = "Experience and involvement"
EXPERIENCE = [
    {
        "role": Draft("AI systems developer"),
        "org": "AI agent platform, contract",
        "dates": "June 2026 to present",
        "text": Draft("I build features for an AI agent platform, including a review loop in which one agent checks another's code changes until they pass, and a single screen for watching every agent at once. Next: infrastructure that fits the platform to each client's business."),
    },
    {
        "role": "Arx, personal project",
        "org": "Self-built study and work planner",
        "dates": "2026",
        "text": Draft("A planner I built for myself that synced uni deadlines from Canvas and scheduled work backwards from them; it is where my development work started."),
    },
    {
        "role": "Customer service and administration",
        "org": "Self-storage business, casual",
        "dates": "December 2022 to present",
        "text": Draft("Sales by phone, email and in person, chasing overdue accounts and sorting out issues on site. I also covered the assistant manager's shifts while the role was vacant."),
    },
    {
        "role": "COVID-19 pathology collection",
        "org": "Pathology provider: testing sites, then hotel quarantine",
        "dates": "2021 to 2022",
        "text": None,
    },
    {
        "role": "Team member",
        "org": "Restaurant chain, Melbourne CBD",
        "dates": "2018 to 2021",
        "text": None,
    },
    {
        "role": "Player, left back",
        "org": "Swinburne Football (Soccer) Club, Metro League 5",
        "dates": "2026",
        "text": None,
    },
]

EDUCATION_HEAD = "Education"
EDUCATION = [   # same fields as EXPERIENCE
    {
        "role": "Bachelor of Arts, Politics, Power and Technology",
        "org": "Swinburne University of Technology",
        "dates": "2026 to present",
        "text": None,
    },
    {
        "role": "Diploma of Arts and Communication (UniLink)",   # Ryan to check the exact name on his transcript
        "org": "Swinburne University of Technology; credited as the first year of the BA",
        "dates": "October 2025 to June 2026",
        "text": None,
    },
]

# ---------------------------------------------------------------- 7. contact
CONTACT_HEAD = "Contact"
CONTACT_LINE = None   # dropped 13 Nov (Ryan)
EMAIL = "103024469@student.swin.edu.au"   # Swinburne address for now (Ryan, 13 Nov); swap for a personal one later

# ---------------------------------------------------------------- 8. footer
AI_NOTE = None   # dropped 12 Nov: Ryan will put an AI statement in the Canvas submission instead
CREDITS = [
    "Set in Newsreader and Source Sans 3, both under the SIL Open Font License (fonts/OFL-*.txt).",
    'Footscray title slide photo: "Saltwater River Crossing Site and Footscray Wharves Precinct" by Sgroey, CC BY-SA 4.0, via Wikimedia Commons.',
    "Campaign screenshots include AI-generated images made for the Not Our Game campaign; they do not show real people.",
]
CREDIT_LINKS = {  # text inside CREDITS that becomes a link
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "Wikimedia Commons": "https://commons.wikimedia.org/wiki/File:Saltwater_River_Crossing_Site_and_Footscray_Wharves_Precinct.jpg",
}

NOT_FOUND = ("Page not found", "That page does not exist. Go back to the home page.")
