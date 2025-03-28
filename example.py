from searcherator import Searcherator
import asyncio

async def main():
    # s = Searcherator("Book 'If Cats Disappeared from the World: A Novel' by 'Genki Kawamura'")
    h = Searcherator("Zusammenfassung Buch 'Demian' von 'Hermann Hesse'", language="de", country="de", num_results=10)
    #await h.print()
    print(await h.urls())


if __name__ == "__main__":
    asyncio.run(main())
