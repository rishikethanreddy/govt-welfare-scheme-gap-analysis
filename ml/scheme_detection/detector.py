import re
from typing import Optional

class SchemeDetector:
    def __init__(self):
        # Define 15 supported schemes and their aliases
        self.scheme_aliases = {
            "PM-KISAN": ["pm kisan", "pm-kisan", "pmkisan", "kisan samman nidhi", "pradhan mantri kisan"],
            "Pradhan Mantri Fasal Bima Yojana (PMFBY)": ["pmfby", "fasal bima", "crop insurance"],
            "PM-KUSUM": ["pm kusum", "pm-kusum", "solar pump", "kusum yojana"],
            "Pradhan Mantri Awas Yojana (PMAY)": ["pmay", "awas yojana", "pm awas", "housing scheme"],
            "Ayushman Bharat - PM-JAY": ["ayushman bharat", "pm-jay", "pmjay", "ayushman card", "health card"],
            "MGNREGA": ["mgnrega", "nrega", "100 days work", "job card"],
            "Pradhan Mantri Jan Dhan Yojana (PMJDY)": ["pmjdy", "jan dhan", "zero balance account"],
            "Pradhan Mantri Mudra Yojana (PMMY)": ["pmmy", "mudra yojana", "mudra loan", "shishu loan", "tarun loan", "kishore loan"],
            "PM SVANidhi": ["svanidhi", "street vendor", "pm svanidhi"],
            "Atal Pension Yojana (APY)": ["apy", "atal pension"],
            "PMJJBY": ["pmjjby", "jeevan jyoti"],
            "PMSBY": ["pmsby", "suraksha bima"],
            "National Social Assistance Programme (NSAP)": ["nsap", "old age pension", "widow pension", "disability pension"],
            "Pradhan Mantri Ujjwala Yojana (PMUY)": ["pmuy", "ujjwala", "gas cylinder scheme", "free gas"],
            "PM Vishwakarma": ["vishwakarma", "artisan scheme"]
        }
        
    def detect_scheme(self, text: str) -> str:
        """
        Detects the most likely scheme from the text based on keyword matching.
        Returns the canonical scheme name or 'Other / Unknown'.
        """
        text = text.lower()
        
        # Check for matches
        for canonical_name, aliases in self.scheme_aliases.items():
            for alias in aliases:
                # Use word boundaries for accurate matching where possible
                # e.g., "\bpm kisan\b"
                # Some aliases might have special chars, so basic string matching is safer for now
                if alias in text:
                    return canonical_name
                    
        return "Other / Unknown"

if __name__ == "__main__":
    detector = SchemeDetector()
    print(detector.detect_scheme("I did not receive my 15th pm-kisan installment.")) # Expected: PM-KISAN
    print(detector.detect_scheme("How to apply for job card?")) # Expected: MGNREGA
