"""Render the portfolio's local SVG panels."""
from base64 import b64encode
from datetime import date, datetime, timedelta
import json
import math
import xml.etree.ElementTree as ET
from svg_canvas import Canvas, ROOT, SETTINGS, WHITE, MUTED, BLUE

DATA = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
PROJECTS = []
for configured in json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8")):
    facts = DATA["featured"][configured["repository"]]
    project = dict(configured)
    project.setdefault("title", facts["name"])
    project.setdefault("description", facts["description"])
    project.setdefault("technologies", [facts["language"]] if facts["language"] else [])
    if not project["description"]:
        raise ValueError(f"Add an accurate description for {facts['name']} in data/projects.json")
    PROJECTS.append(project)
WRITTEN = set()
LANGUAGE_COLORS = {"JavaScript": "#f1e05a", "Java": "#d99245", "TypeScript": "#58a6ff", "CSS": "#a371f7", "HTML": "#e67e55", "C": "#a7b2bf", "Python": "#5aa6d1", "Other": "#708396"}


def save(c, name):
    c.save(name)
    WRITTEN.add(name)


def day_label(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y")


def repository_date(facts):
    if facts.get("pushed_at"):
        return "Pushed " + day_label(facts["pushed_at"])
    return "Updated " + day_label(facts["updated_at"])


def fit(c, text, width, size=16, mono=False, weight=500):
    if c.measure(text, size, mono, weight) <= width:
        return text
    while text and c.measure(text + "...", size, mono, weight) > width:
        text = text[:-1]
    return text.rstrip() + "..."


def svg_icon(c, technology, x, y, size):
    root = ET.parse(ROOT / f"assets/icons/{technology}.svg").getroot()
    # Independent Devicon files can reuse gradient IDs such as "a" or "b".
    ids = {node.get("id"): technology+"-"+node.get("id") for node in root.iter() if node.get("id")}
    for node in root.iter():
        for key, value in list(node.attrib.items()):
            if key == "id":
                node.set(key, ids[value])
            else:
                for old, new in ids.items():
                    value = value.replace("url(#"+old+")", "url(#"+new+")")
                    if key.endswith("href") and value == "#"+old:
                        value = "#"+new
                node.set(key, value)
    for key, value in {"x": x, "y": y, "width": size, "height": size}.items():
        root.set(key, str(value))
    c.add(ET.tostring(root, encoding="unicode"))


def typing(c, x, y, width, mobile, static):
    size = 15 if mobile else 17
    lines = SETTINGS["typing_lines"]
    duration = len(lines)*5
    for index, text in enumerate(lines[:1] if static else lines):
        text = fit(c, text, width, size, mono=True)
        tw = c.measure(text, size, True)
        c.add(f'<defs><clipPath id="typing-{index}"><rect x="{x}" y="{y-size-4}" width="{tw+2}" height="{size+10}">')
        if not static:
            # Each line gets one five-second slot in the shared cycle.
            slot = 5/duration
            c.add(f'<animate attributeName="width" values="0;{tw+2};{tw+2};0" keyTimes="0;{slot*.55};{slot*.9};1" begin="{index*5}s" dur="{duration}s" repeatCount="indefinite"/>')
        c.add('</rect></clipPath></defs>')
        c.add(f'<g clip-path="url(#typing-{index})" opacity="{1 if index == 0 else 0}">')
        if not static and len(lines) > 1:
            c.add(f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{slot*.9};{slot};1" begin="{index*5}s" dur="{duration}s" repeatCount="indefinite"/>')
        c.text(text, x, y, size, BLUE, 500, True)
        c.add('</g>')


def hero(mobile=False, static=False):
    w, h = (480, 384) if mobile else (960, 300)
    c = Canvas(w, h, SETTINGS["name"] + " — " + SETTINGS["role"], SETTINGS["identity"] + ". " + " ".join(SETTINGS["typing_lines"]))
    c.shell()
    c.rect(25, 25, w-50, h-50, "#0b1119", 20, "#2c6086", fill_opacity=".66")
    cx, cy, r = (73, 80, 28) if mobile else (112, 128, 48)
    c.add(f'<defs><clipPath id="avatar"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>')
    avatar = b64encode((ROOT / "assets/avatar.jpg").read_bytes()).decode()
    c.add(f'<circle cx="{cx}" cy="{cy}" r="{r+4}" fill="none" stroke="{BLUE}" stroke-width="1.5"/>')
    c.add(f'<image x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#avatar)" xlink:href="data:image/jpeg;base64,{avatar}"/>')
    if mobile:
        c.text("@" + SETTINGS["username"], 117, 77, 14, MUTED, 500, True)
        c.text(SETTINGS["identity"].upper(), 117, 98, 10.5, BLUE, 600, True, .3)
        c.text(SETTINGS["name"], 46, 168, 38, WHITE, 800)
        c.text(SETTINGS["role"], 46, 205, 19, MUTED)
        c.line(46, 236, 434, 236)
        c.text("$", 46, 289, 17, BLUE, 600, True)
        typing(c, 69, 289, 365, True, static)
        c.text("REACT / SPRING BOOT / MYSQL", 46, 329, 11, MUTED, 500, True, .6)
    else:
        c.text("@" + SETTINGS["username"], 198, 84, 13, MUTED, 600, True, 1.1)
        c.text(SETTINGS["name"], 194, 148, 58, WHITE, 800)
        c.text(SETTINGS["identity"], 198, 184, 20, MUTED)
        c.text(SETTINGS["role"], 198, 212, 20, MUTED)
        c.text("$", 48, 265, 17, BLUE, 600, True)
        typing(c, 72, 265, 815, False, static)
        c.text("FULL-STACK / IN PROGRESS", 911, 63, 9, BLUE, 500, True, align="right")
    suffix = ("-mobile" if mobile else "") + ("-static" if static else "")
    save(c, "hero" + suffix + ".svg")


def toolkit(mobile=False):
    groups = SETTINGS["technology_groups"]
    w = 480 if mobile else 960
    heights = [40+math.ceil(len(g["items"])/3)*79 if mobile else math.ceil(len(g["items"])/3)*65 for g in groups]
    c = Canvas(w, 146+sum(heights), "Technology stack and project tooling", "; ".join(g["label"] + ": " + ", ".join(i["label"] for i in g["items"]) for g in groups))
    c.shell(); c.header("01", "STACK.CONFIG", "The toolkit", mobile)
    top = 120
    for group, height in zip(groups, heights):
        c.text(group["label"].upper(), 30, top+(15 if mobile else 31), 11, BLUE, 600, True, .7)
        for i, item in enumerate(group["items"]):
            column, row = i % 3, i // 3
            if mobile:
                x, y = 30+column*140, top+row*79
                c.rect(x, y+30, 131, 67, "#101822", 10, "#24384c")
                svg_icon(c, item["icon"], x+12, y+45, 24)
                c.text(fit(c, item["label"], 79, 13, weight=600), x+45, y+61, 13, WHITE, 600)
            else:
                x, y = 233+column*232, top+row*65
                c.rect(x, y+1, 215, 49, "#101822", 10, "#24384c")
                svg_icon(c, item["icon"], x+14, y+12, 27)
                c.text(fit(c, item["label"], 145, 16, weight=600), x+56, y+32, 16, WHITE, 600)
        top += height
    save(c, "stack-mobile.svg" if mobile else "stack.svg")


def project_header(mobile=False):
    w = 480 if mobile else 960
    c = Canvas(w, 116, "Featured repositories", "Curated learning projects. Each card links directly to its repository; available demos are linked below.")
    c.shell()
    c.text("02 / PROJECTS.LIST", 30, 37, 12, BLUE, 600, True, 1.4)
    c.text("Selected work", 30, 77, 27, WHITE, 800)
    if not mobile:
        c.text(f"{len(PROJECTS):02d} repositories / curated, not ranked", 930, 77, 12, MUTED, 500, True, align="right")
    save(c, "projects-header-mobile.svg" if mobile else "projects-header.svg")


def project_card(project, index):
    facts = DATA["featured"][project["repository"]]
    c = Canvas(480, 290, facts["name"] + " — " + project["title"], project["description"] + f" Primary language: {facts['language']}. {facts['stars']} stars; {facts['forks']} forks. " + repository_date(facts) + ".")
    c.shell()
    c.rect(1, 1, 478, 36, "#151f2c", 21)
    c.rect(1, 22, 478, 15, "#151f2c")
    c.line(1, 37, 479, 37, "#2a4c6a")
    c.add(f'<circle cx="19" cy="19" r="2.5" fill="{BLUE}"/>')
    c.text(facts["name"], 32, 24, 12, MUTED, 500, True)
    c.text(f"{index+1:02d}", 458, 24, 11, BLUE, 500, True, align="right")
    c.text(fit(c, project["title"], 432, 25, weight=800), 24, 80, 25, WHITE, 800)
    c.paragraph(project["description"], 24, 112, 432, 16, 24, max_lines=3)
    tx = 24
    for tech in project["technologies"]:
        tw = c.measure(tech, 11, True)+18
        c.rect(round(tx,2), 185, round(tw,2), 24, "#142337", 12, "#2b4d6b")
        c.text(tech, tx+9, 201, 11, BLUE, 500, True)
        tx += tw+8
    c.line(24, 225, 456, 225)
    language = facts["language"] or "Not reported"
    c.add(f'<circle cx="29" cy="245" r="4" fill="{LANGUAGE_COLORS.get(language, BLUE)}"/>')
    c.text(language, 41, 249, 12, WHITE, 600)
    if SETTINGS["show_repository_counts"]:
        c.text(f"{facts['stars']} stars / {facts['forks']} forks", 456, 249, 11, MUTED, 500, True, align="right")
    c.text(repository_date(facts), 24, 273, 10, MUTED, 500, True)
    c.text("VIEW SOURCE  /", 456, 273, 10, BLUE, 600, True, align="right")
    save(c, f"project-{project['repository'].lower()}.svg")


def statistics(mobile=False):
    w, columns, rh = (480, 2, 112) if mobile else (960, 4, 112)
    h = 165+math.ceil(8/columns)*rh
    c = Canvas(w, h, "GitHub at a glance — verified public statistics", f"{DATA['contributions_since_joining']} visible contributions since {DATA['joined_year']}; {DATA['public_repositories']} public repositories; {DATA['followers']} followers and {DATA['following']} following. Counts are dated snapshots.")
    c.shell(); c.header("03", "GITHUB.SNAPSHOT", "GitHub at a glance", mobile)
    metrics = [(DATA["contributions_since_joining"], "CONTRIBUTIONS", f"since joining in {DATA['joined_year']}"), (DATA["public_repositories"], "PUBLIC REPOS", "including this profile"), (DATA["followers"], "FOLLOWERS", "public profile"), (DATA["following"], "FOLLOWING", "public profile"), (DATA["stars_on_original_repos"], "STARS RECEIVED", "original public repos"), (DATA["public_pull_requests"], "PUBLIC PULL REQUESTS", "authored / indexed"), (DATA["public_issues"], "PUBLIC ISSUES", "authored / indexed"), (DATA["streak"]["current"], "CURRENT STREAK", "days / UTC calendar")]
    cw = (w-60)/columns
    for i, (value, label, scope) in enumerate(metrics):
        x, y = 30+(i%columns)*cw, 121+(i//columns)*rh
        c.rect(round(x,2), y, round(cw-12,2), rh-12, "#101822", 12, "#24384c")
        c.text(label, x+14, y+22, 9 if mobile else 9.5, BLUE, 600, True, .1)
        c.text(f"{value:,}", x+14, y+62, 33, WHITE, 800)
        c.text(scope, x+14, y+84, 10, MUTED)
    c.text("Updated " + day_label(DATA["updated_at"]) + " UTC", 30, h-18, 10, MUTED, 500, True)
    save(c, "statistics-mobile.svg" if mobile else "statistics.svg")


def language_rows():
    items = list(DATA["languages"].items())
    return items if len(items) <= 6 else items[:5]+[("Other",sum(count for _,count in items[5:]))]


def languages(mobile=False):
    rows = language_rows()
    w, h = (480, 430) if mobile else (960, 333)
    c = Canvas(w, h, "Most-used programming languages by code bytes", "Byte totals from original public repositories, excluding forks and generated profile code. Not a proficiency rating or time-spent measure.")
    c.shell(); c.header("04", "LANGUAGES.BYTES", "Languages across my projects", mobile)
    total = sum(count for _,count in rows)
    x = 30
    for language, count in rows:
        width = (w-60)*count/total if total else 0
        c.rect(round(x,2), 128, round(width,2), 14, LANGUAGE_COLORS.get(language, BLUE))
        x += width
    cols = 2 if mobile else 3
    cw = (w-60)/cols
    for i, (language, count) in enumerate(rows):
        x, y = 30+(i%cols)*cw, 186+(i//cols)*65
        c.add(f'<circle cx="{x+5}" cy="{y-5}" r="4" fill="{LANGUAGE_COLORS.get(language,BLUE)}"/>')
        c.text(language, x+18, y, 15, WHITE, 600)
        c.text(f"{100*count/total:.1f}%" if total else "0%", x+18, y+24, 14, MUTED, 500, True)
    c.text("PUBLIC SOURCE CODE / BYTES, NOT PROFICIENCY", 30, h-40, 9, BLUE, 500, True, .4)
    c.text("Excludes forks and this generated profile.", 30, h-19, 11, MUTED)
    save(c, "languages-mobile.svg" if mobile else "languages.svg")


def route(points, step):
    first = points[0]
    grid = [first]
    x,y = first
    for tx,ty in points[1:]:
        while x != tx:
            x += 1 if tx>x else -1
            grid.append((x,y))
        while y != ty:
            y += 1 if ty>y else -1
            grid.append((x,y))
    grid += [(x,8),(first[0],8),first]
    return "M" + " L".join(f"{(x-first[0])*step:.2f} {(y-first[1])*step:.2f}" for x,y in grid) + " Z", first


def draw_grid(c, days, first_sunday, first_column, count, y, static, mobile, identifier):
    left, right = 58, c.width-30
    step = (right-left)/count
    size = step-3
    colors = ["#1b2531", "#203f60", "#2c6090", "#3983bd", BLUE]
    for label, row in [("Mon",1),("Wed",3),("Fri",5)]:
        c.text(label, left-9, y+row*step+size*.85, 9 if mobile else 10, MUTED, 500, True, align="right")
    previous_month = None
    active = []
    for day in days:
        day_date = date.fromisoformat(day["date"])
        offset = (day_date-first_sunday).days
        col,row = offset//7-first_column, offset%7
        if not 0 <= col < count:
            continue
        if day_date.day <= 7 and day_date.month != previous_month and col < count-1:
            c.text(day_date.strftime("%b"), left+col*step, y-12, 11, MUTED, 500, True)
            previous_month = day_date.month
        c.rect(round(left+col*step,2), round(y+row*step,2), round(size,2), round(size,2), colors[day["level"]], 2)
        if day["level"]:
            active.append((col,row))
    if active and not static:
        d, first = route(active, step)
        c.add(f'<defs><path id="route-{identifier}" d="{d}"/></defs>')
        origin = (left+first[0]*step+size/2, y+first[1]*step+size/2)
        # Place the still fallback at a real active day, rather than SVG origin.
        c.add(f'<g transform="translate({origin[0]:.2f} {origin[1]:.2f})">')
        for segment in range(5,-1,-1):
            c.add(f'<g opacity="{1-segment*.13:.2f}"><rect x="{-size/2:.2f}" y="{-size/2:.2f}" width="{size:.2f}" height="{size:.2f}" rx="3" fill="{WHITE if segment == 0 else BLUE}"/>')
            if segment == 0:
                c.add('<circle cx="-2" cy="-1.4" r="1.1" fill="#15385b"/><circle cx="2" cy="-1.4" r="1.1" fill="#15385b"/>')
            c.add(f'<animateMotion dur="48s" begin="{-12-segment*.18:.2f}s" repeatCount="indefinite" calcMode="paced"><mpath xlink:href="#route-{identifier}"/></animateMotion></g>')
        c.add('</g>')


def calendar(mobile=False, static=False, light=False):
    w,h = (480,572) if mobile else (960,406)
    c = Canvas(w,h,"Contribution history — last year",f"{DATA['contributions_last_year']} contributions in the last year. Longest streak in the displayed grid: {DATA['streak']['longest_in_grid']} days. Actual GitHub intensity levels, captured {DATA['updated_at']}.")
    c.light = light
    c.shell(); c.header("05", "CONTRIBUTIONS.CALENDAR", "Your year in code", mobile)
    c.text(f"{DATA['contributions_last_year']} contributions / {DATA['active_days_in_grid']} active days",30,131,14,WHITE,600)
    first_sunday = date.fromisoformat(DATA["calendar_start"])
    first_sunday -= timedelta(days=(first_sunday.weekday()+1)%7)
    cols = (date.fromisoformat(DATA["calendar_end"])-first_sunday).days//7+1
    if mobile:
        split = cols//2
        draw_grid(c,DATA["days"],first_sunday,0,split,178,static,True,"first")
        draw_grid(c,DATA["days"],first_sunday,split,cols-split,350,static,True,"second")
        footer = 508
    else:
        draw_grid(c,DATA["days"],first_sunday,0,cols,178,static,False,"year")
        footer = 348
    c.text("Longest streak: " + str(DATA["streak"]["longest_in_grid"]) + " days in this grid",30,footer,11,MUTED)
    c.text("Less", w-173,footer,9,MUTED,500,True)
    for i,color in enumerate(["#1b2531","#203f60","#2c6090","#3983bd",BLUE]):
        c.rect(w-139+i*15,footer-9,10,10,color,2)
    c.text("More",w-30,footer,9,MUTED,500,True,align="right")
    c.text(DATA["calendar_start"]+" / "+DATA["calendar_end"],30,footer+25,10,MUTED,500,True)
    c.text("Updated "+day_label(DATA["updated_at"])+" UTC",30,footer+46,10,MUTED,500,True)
    suffix = ("-mobile" if mobile else "")+("-light" if light else "")+("-static" if static else "")
    save(c,"calendar"+suffix+".svg")


def recent(mobile=False):
    w = 480 if mobile else 960
    updates, events = DATA["recent_updates"],DATA["recent_events"]
    h = 266+len(updates)*64+len(events)*83 if mobile else 211+max(len(updates)*70,len(events)*84)
    c = Canvas(w,h,"Recent repository updates and public activity", "Repository push dates and a limited public event feed. "+"; ".join(e["created_at"][:10]+": "+e["summary"]+" in "+e["repository"] for e in events))
    c.shell();c.header("06","ACTIVITY.FEED","From the workbench",mobile)
    c.text("RECENT REPOSITORY UPDATES",30,136,11,BLUE,600,True,.5)
    for i,item in enumerate(updates):
        y=167+i*(64 if mobile else 70)
        c.text(fit(c,item["repository"],400,18,weight=700),30,y,18,WHITE,700)
        c.text(day_label(item["pushed_at"])+" / "+(item["language"] or "Not reported"),30,y+23,11,MUTED,500,True)
    ex = 30 if mobile else 500
    ey = 177+len(updates)*64 if mobile else 136
    c.text("PUBLIC EVENTS / LAST 30 DAYS",ex,ey,11,BLUE,600,True,.5)
    if not events:
        c.text("No events returned in this window.",ex,ey+33,14,MUTED)
    for i,item in enumerate(events):
        y=ey+33+i*83
        c.text(fit(c,item["summary"],w-ex-30,15,weight=600),ex,y,15,WHITE,600)
        c.text(fit(c,item["repository"],w-ex-30,12,mono=True),ex,y+22,12,MUTED,500,True)
        c.text(day_label(item["created_at"])+" UTC",ex,y+42,10,MUTED,500,True)
    c.text("DATED SNAPSHOT / THE EVENT FEED MAY BE DELAYED",30,h-21,9,BLUE,500,True,.3)
    save(c,"recent-mobile.svg" if mobile else "recent.svg")


def footer(mobile=False):
    w = 480 if mobile else 960
    c=Canvas(w,126,"Contact and connect", "Connect with "+SETTINGS["name"]+" using the links beneath this panel.")
    c.shell()
    c.text("07 / CONNECT",w/2,37,11,BLUE,600,True,1.3,align="center")
    c.text("Let's build something useful.",w/2,80,23 if mobile else 29,WHITE,800,align="center")
    save(c,"footer-mobile.svg" if mobile else "footer.svg")
