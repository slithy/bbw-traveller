from cogst5.library_data import LibraryData


class Library:
    def __init__(self):
        libraryData = "None"

    def search(self, term):
        # Check first for exact matches
        exact_match = [k for key, k in enumerate(LibraryData) if term.lower() == k.lower()]

        # Otherwise, make a list of partial matches
        partial_match = [k for key, k in enumerate(LibraryData) if term.lower() in k.lower()]

        if len(partial_match) == 0:
            return f"Library search for *{term}*: data is not available."

        if len(partial_match) == 1:
            return (
                f"**Information.** Library data available on **{partial_match[0]}**:\n{LibraryData[partial_match[0]]}"
            )

        if len(exact_match) == 1:
            partial_match.remove(exact_match[0])
            all_matches = "\n • ".join(partial_match)
            see_also = "\n**See also:**" if (LibraryData[exact_match[0]].find("See also:") == -1) else ""
            return f"**Information.** Library data available on **{exact_match[0]}**:\n{LibraryData[exact_match[0]]}{see_also}\n • {all_matches}"

        if len(partial_match) > 10:
            return f"**Information.** Library contains {len(partial_match)} data items pertaining to *{term}*. Please be more specific."
        else:
            all_matches = "\n • ".join(partial_match)
            return f"**Information.** Library contains {len(partial_match)} data items pertaining to *{term}*. Please specify:\n • {all_matches}"
