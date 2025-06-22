import string
import re

BAD_WORDS = {
    # --- sexual / scatalogical profanity --------------------------------
    "anal", "anus", "arse", "arsebandit", "arsehole", "arselicker", "arsewipe",
    "ass", "asses", "asshole",
    "bastard", "bellend", "bollock", "bollocks", "bugger",
    "clusterfuck", "cock", "cockhead", "cum", "cumbucket", "cumshot", "cumming",
    "cunt",
    "dick", "dickhead", "dildo", "dipshit", "doggy", "doggystyle", "douche", "douchebag",
    "fuck", "fucker", "fucking", "fucked", "foreskin",
    "handjob", "ho", "jizz",
    "knob", "knobend", "knobhead", "knobjockey",
    "minge", "mofo", "motherfucker", "motherfucking",
    "numbnuts",
    "prick", "pussy",
    "rimjob",
    "shit", "shitbag", "shitface", "shitfaced", "shithead", "shitstorm", "shitty", "shite", "shitehead",
    "slag", "slut", "spunk",
    "tosser", "twat", "twathead", "twatwaffle", "twats", "twatso",
    "wank", "wanker", "wankpuffin", "wankstain",
    "whore", "whorebag", "whoreface",

    # --- hateful or discriminatory slurs --------------------------------
    "beaner", "chink", "crip", "dyke", "fag", "faggot",
    "gimp", "gook",
    "kike",
    "nigga", "nigger",
    "paki",
    "raghead", "retard",
    "spaz", "spic",
    "tard", "tranny",
    "wetback", "wop",
}

def contains_bad_words(tokens):
    return any(w in BAD_WORDS for w in tokens)

_word_re = re.compile(r"[a-z0-9']+", re.I)

def check_profanity(text):
    """Check if text contains profanity."""
    if not text:
        return False
    
    words = _word_re.findall(text.lower())   # ['this','is','a','damn','bad','review','fuck']
    return any(word in BAD_WORDS for word in words) 

if __name__ == "__main__":
    print(check_profanity("This is a damn bad review, fuck."))