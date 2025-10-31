import csv, random, re
from datetime import date, timedelta

random.seed(303)

CATS = [
    "Groceries","Coffee","Utilities","Rent","Internet","Phone",
    "Office Supplies","Dining","Transportation","Fuel","Pharmacy",
    "Entertainment","Fitness","Insurance","Travel","Electronics",
    "Clothing","Household","Parking","Education"
]

VENDORS = {
    "Groceries": ["Metro","Loblaws","No Frills","Walmart","Whole Foods","FreshCo","Food Basics","Farm Boy"],
    "Coffee": ["Starbucks","Tim Hortons","Second Cup","Bridgehead","Balzac's","Coffee Culture"],
    "Utilities": ["Toronto Hydro","London Hydro","Enbridge Gas","Alectra Utilities","Hydro One"],
    "Rent": ["Middlesex Property Mgmt","Campus Rentals","GreenLeaf Properties","Dream Properties","Woodland Apartments"],
    "Internet": ["Rogers","Bell","TekSavvy","Start.ca","Virgin Plus","Fido Home"],
    "Phone": ["Rogers Wireless","Bell Mobility","Freedom Mobile","Koodo Mobile","Telus Mobility"],
    "Office Supplies": ["Staples","Amazon","Grand & Toy","Walmart","Dollarama"],
    "Dining": ["Chipotle","McDonalds","Subway","Thai Express","Kinka Izakaya","Freshii","A&W","KFC"],
    "Transportation": ["Uber","Lyft","UP Express","GO Transit","London Transit","VIA Rail"],
    "Fuel": ["Esso","Shell","Petro-Canada","Circle K","Costco Gas"],
    "Pharmacy": ["Shoppers Drug Mart","Rexall","Guardian Pharmacy","Pharma Plus"],
    "Entertainment": ["Cineplex","Steam","Spotify","Apple Services","Netflix","PlayStation Store"],
    "Fitness": ["GoodLife Fitness","Planet Fitness","YMCA","LA Fitness","Anytime Fitness"],
    "Insurance": ["Desjardins Insurance","TD Insurance","RBC Insurance","Intact Insurance"],
    "Travel": ["Air Canada","Porter Airlines","VIA Rail","Expedia","Flair Airlines","WestJet"],
    "Electronics": ["Best Buy","Canada Computers","The Source","Apple Store","Memory Express"],
    "Clothing": ["Uniqlo","H&M","Zara","Winners","Gap","Old Navy"],
    "Household": ["IKEA","Canadian Tire","Home Depot","Home Hardware","Bed Bath & Beyond"],
    "Parking": ["Honkmobile","City of London Parking","Green P Parking","Indigo Parking"],
    "Education": ["Western Bookstore","Coursera","Udemy","edX","LinkedIn Learning"]
}

DESCS = {
    "Groceries": ["Weekly grocery run","Fresh produce + pantry items","Snacks and staples","Milk, eggs, bread","Grocery top-up"],
    "Coffee": ["Latte and pastry","Iced coffee","Cold brew","Americano","Cappuccino","Mocha"],
    "Utilities": ["Monthly utility bill","Electricity usage","Gas service charge","Electric bill for apt"],
    "Rent": ["Monthly rent payment","Rent for unit 3B","Apartment rent"],
    "Internet": ["Monthly internet bill","Internet plan charge","Modem rental fee"],
    "Phone": ["Mobile plan payment","Data overage fee","Device financing"],
    "Office Supplies": ["Pens and notebooks","Printer paper (500ct)","Desk organizer","Highlighters + sticky notes"],
    "Dining": ["Lunch combo","Dinner with friends","Takeout order","Meal deal","Student discount meal"],
    "Transportation": ["Ride to campus","Airport ride","Commute to work","Bus pass reload"],
    "Fuel": ["Gas fill-up","Fuel top-up","Premium gas purchase"],
    "Pharmacy": ["Vitamins and essentials","OTC medicine","Personal care items"],
    "Entertainment": ["Movie tickets","Game purchase","Subscription renewal","Streaming plan"],
    "Fitness": ["Gym membership","Drop-in class","Monthly dues"],
    "Insurance": ["Monthly premium","Policy payment","Auto insurance"],
    "Travel": ["Flight booking","Train ticket","Hotel deposit","Baggage fee"],
    "Electronics": ["USB-C cable","Headphones","Laptop accessory","Phone case"],
    "Clothing": ["T-shirt and jeans","Seasonal jacket","Athleisure","Socks 3-pack"],
    "Household": ["Cleaning supplies","Home essentials","Kitchenware","Light bulbs"],
    "Parking": ["Parking session","Evening parking","All-day parking"],
    "Education": ["Textbook","Course enrollment","Exam fee","Cert prep"]
}

LOC = ["London ON","Downtown","Campus","Masonville","Online","Store #214","Richmond St"]
MOD = ["promo","student","receipt","order","invoice","ref","txn","branch"]

def mix_desc(base: str) -> str:
    parts = [base]
    if random.random() < 0.5: parts.append(random.choice(LOC))
    if random.random() < 0.4: parts.append(f"{random.choice(MOD)} #{random.randint(1000,9999)}")
    txt = " ".join(parts)
    if random.random() < 0.25:
        txt = re.sub(r" ", "  ", txt, count=random.randint(1,3))
    r = random.random()
    if   r < 0.15: txt = txt.lower()
    elif r < 0.30: txt = txt.title()
    return txt

def rand_date() -> str:
    d = date.today() - timedelta(days=random.randint(0, 270))
    return d.strftime("%Y-%m-%d")

def amount_for(cat: str) -> float:
    if cat == "Rent": return round(random.uniform(700, 1900), 2)
    if cat in ["Utilities","Internet","Phone","Insurance","Fitness","Education"]: return round(random.uniform(12, 220), 2)
    if cat == "Travel": return round(random.uniform(60, 900), 2)
    if cat in ["Electronics","Clothing","Household"]: return round(random.uniform(10, 500), 2)
    return round(random.uniform(3, 140), 2)

rows = []
for cat in CATS:
    for _ in range(20):  # 20 per category = 400
        vendor = random.choice(VENDORS[cat])
        vendor = f"{vendor} #{random.randint(100, 899)}" if random.random() < 0.35 else vendor
        desc = mix_desc(random.choice(DESCS[cat]))
        rows.append({
            "vendor": vendor,
            "description": desc,
            "category": cat,
            "date": rand_date(),
            "amount": amount_for(cat)
        })

out = "training_data_400.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["vendor","description","category","date","amount"])
    w.writeheader(); w.writerows(rows)

print(f"Wrote {len(rows)} rows to {out}")
