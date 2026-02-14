"""
Italian main companies list - FTSE MIB index constituents and other major Italian companies.
"""

# Major Italian companies from the FTSE MIB index and other significant firms.
# Each entry: (company_name, search_keywords, sector)
ITALIAN_COMPANIES = [
    # Financial Services & Banking
    ("Intesa Sanpaolo", ["Intesa Sanpaolo"], "Banking"),
    ("UniCredit", ["UniCredit"], "Banking"),
    ("Mediobanca", ["Mediobanca"], "Banking"),
    ("Banco BPM", ["Banco BPM"], "Banking"),
    ("BPER Banca", ["BPER Banca"], "Banking"),
    ("FinecoBank", ["FinecoBank", "Fineco"], "Banking"),
    ("Generali", ["Generali assicurazioni", "Assicurazioni Generali"], "Insurance"),
    ("Unipol", ["Unipol", "UnipolSai"], "Insurance"),
    ("Poste Italiane", ["Poste Italiane"], "Financial Services"),

    # Energy & Utilities
    ("Eni", ["Eni SpA", "Eni petrolio"], "Energy"),
    ("Enel", ["Enel", "Enel energia"], "Utilities"),
    ("Snam", ["Snam"], "Energy Infrastructure"),
    ("Terna", ["Terna rete elettrica"], "Utilities"),
    ("Italgas", ["Italgas"], "Utilities"),
    ("A2A", ["A2A energia"], "Utilities"),
    ("Hera", ["Hera gruppo"], "Utilities"),
    ("Saipem", ["Saipem"], "Energy Services"),
    ("Tenaris", ["Tenaris"], "Energy Equipment"),

    # Automotive & Industrial
    ("Stellantis", ["Stellantis", "Stellantis Italia"], "Automotive"),
    ("Ferrari", ["Ferrari NV", "Ferrari auto"], "Automotive"),
    ("Pirelli", ["Pirelli"], "Automotive Components"),
    ("Iveco Group", ["Iveco Group"], "Commercial Vehicles"),
    ("CNH Industrial", ["CNH Industrial"], "Industrial Machinery"),
    ("Leonardo", ["Leonardo difesa", "Leonardo aerospazio"], "Aerospace & Defense"),
    ("Prysmian", ["Prysmian"], "Industrial"),

    # Luxury & Fashion
    ("Moncler", ["Moncler"], "Luxury Fashion"),
    ("Brunello Cucinelli", ["Brunello Cucinelli"], "Luxury Fashion"),
    ("Salvatore Ferragamo", ["Salvatore Ferragamo"], "Luxury Fashion"),
    ("Tod's", ["Tod's gruppo"], "Luxury Fashion"),

    # Technology & Telecom
    ("STMicroelectronics", ["STMicroelectronics"], "Semiconductors"),
    ("Telecom Italia", ["Telecom Italia", "TIM telecom"], "Telecommunications"),
    ("Nexi", ["Nexi pagamenti"], "Fintech"),
    ("Reply", ["Reply SpA"], "IT Services"),

    # Food & Beverage
    ("Campari", ["Davide Campari", "Campari Group"], "Beverages"),
    ("Barilla", ["Barilla"], "Food"),
    ("Ferrero", ["Ferrero"], "Food"),
    ("Lavazza", ["Lavazza caffè"], "Beverages"),

    # Healthcare & Pharma
    ("Recordati", ["Recordati farmaceutica"], "Pharmaceuticals"),
    ("DiaSorin", ["DiaSorin"], "Diagnostics"),
    ("Amplifon", ["Amplifon"], "Medical Devices"),

    # Infrastructure & Real Estate
    ("Atlantia", ["Atlantia"], "Infrastructure"),
    ("Webuild", ["Webuild", "Webuild costruzioni"], "Construction"),
]


def get_all_companies():
    """Return the full list of companies."""
    return ITALIAN_COMPANIES


def get_companies_by_sector(sector):
    """Return companies filtered by sector."""
    return [c for c in ITALIAN_COMPANIES if c[2].lower() == sector.lower()]


def get_sectors():
    """Return a list of unique sectors."""
    return sorted(set(c[2] for c in ITALIAN_COMPANIES))


def get_company_names():
    """Return just the company names."""
    return [c[0] for c in ITALIAN_COMPANIES]
