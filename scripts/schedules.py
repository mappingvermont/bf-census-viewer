"""What differs between census years: the CSV columns, census day, tile descriptions and how to fill each column.

A town picks its schedule with `year` in town.json (default 1900). transcribe_batch.py builds the prompt from
these; build_csv.py uses `census_day` for the age check.
"""
from types import SimpleNamespace

_1900_HEADER = (
    "image,ed,sheet,line,street,house_num,dwelling,dwelling_renum,family,family_renum,"
    "surname,given,relation,race,sex,birth_month,birth_year,age,marital,years_married,"
    "children_born,children_living,birthplace,father_bp,mother_bp,immig_year,years_in_us,"
    "naturalization,occupation,months_unemployed,school_months,can_read,can_write,"
    "speaks_english,home_owned_rented,home_free_mortgaged,farm_or_house,farm_schedule,"
    "uncertain,notes").split(",")

_1900_GUIDE = """\
- `image` = PAGE.jpg, `ed` = the page's enumeration district (the part of PAGE before the dash), `sheet` = \
e.g. 42B, `line` = printed line number.
- `street`: from the vertical street column, written on **every** row (e.g. {streets}). Bare name, no "St".
- `house_num`: only on the first row of a dwelling that has one; blank otherwise.
- `dwelling` / `family` are the enumerator's numbers in **dark ink, lower in the cell**. `dwelling_renum` / \
`family_renum` are the **lighter numbers above them** (a later renumbering). Fill these only on the row where \
they're written.
- Dittos: leave `surname` blank when the page has a dash under the surname. Leave `dwelling`/`house_num` blank \
when a new family shares the dwelling above (only a family number is written). On the page's first line, use `^` \
for a dwelling, house or family number that comes from the previous sheet.
- Ignore the grey tally marks written by the census office over names and relations (e.g. pf-3, 4-2, 1/3, 16, 3-6).
- Months: Jan Feb Mar Apr May June July Aug Sept Oct Nov Dec. Write Unknown for "Un". Infant ages stay as \
fractions, e.g. 8/12.
- Codes: sex M/F, race as written (W, B, ...), marital S/M/Wd/D; naturalization, ownership and farm codes as \
written (Na, Pa, Al, O/R, F/M, H/F).
- Birthplaces: full names (Vermont, New Hampshire, Massachusetts, New York, Ireland, England, Scotland, \
Germany, ...). Keep `Canada (Fr)` / `Canada (Eng)` exactly as written; plain Canada if the page doesn't say \
which. Blank if the page is blank, Unknown if it says unknown.
- Occupation in plain words as written (Laborer paper mill, At school). Literacy is Yes/No.
- Census day was 1 June 1900: age should equal completed years on that day. If the age and birth date \
disagree, look again; if the page really says it, keep what's written and explain in `notes`.
- `uncertain` = 1 if any cell in the row is a guess, else 0. In `notes`, say which cell and the alternative \
reading. Never invent a value: leave unreadable cells blank and flag them."""

_1910_HEADER = (
    "image,ed,sheet,line,street,house_num,dwelling,family,surname,given,relation,sex,race,age,"
    "marital,years_married,children_born,children_living,birthplace,father_bp,mother_bp,"
    "tongue,father_tongue,mother_tongue,immig_year,naturalization,language,occupation,industry,"
    "employer_class,out_of_work,weeks_unemployed,can_read,can_write,in_school,home_owned_rented,"
    "home_free_mortgaged,farm_or_house,farm_schedule,veteran,blind,deaf_dumb,"
    "uncertain,notes").split(",")

_1910_GUIDE = """\
The 1910 form's columns, left to right: street and house number (unnumbered), then 1 dwelling number, 2 family \
number, 3 name, 4 relationship, 5 sex, 6 color or race, 7 age, 8 marital, 9 years of present marriage, 10-11 \
mother of how many children (born, now living), 12-14 place of birth (person, father, mother), 15 year of \
immigration, 16 naturalized or alien, 17 whether able to speak English or if not the language spoken, 18 trade \
or profession, 19 industry, 20 employer / worker / own account, 21 out of work on April 15 1910, 22 weeks out \
of work in 1909, 23 can read, 24 can write, 25 attended school since Sept 1 1909, 26 owned or rented, 27 free \
or mortgaged, 28 farm or house, 29 farm schedule number, 30 Union or Confederate veteran, 31 blind, 32 deaf and \
dumb. There is no birth month or year on this form.

- `image` = PAGE.jpg, `ed` = the page's enumeration district (the part of PAGE before the dash), `sheet` = \
the part after the dash (e.g. 04B), `line` = printed line number.
- `street`: from the vertical street column, written on **every** row. Bare name, no "St". Streets in this \
town include {streets}. The street names are hurried cursive, so before writing a name that isn't on this list, \
check whether it is a misreading of one that is (e.g. "Nartle Sh" is North St). If the street is still unclear, \
say so in `notes` on the first row of that street only, not on every row.
- `house_num`: only on the first row of a dwelling that has one; blank otherwise. Read these carefully: they \
are what places each household on the map. The STREET image also shows the house number column next to the \
printed line numbers.
- `dwelling` / `family`: the numbers in columns 1 and 2, only on the row where they're written.
- Dittos: leave `surname` blank when the page has a dash or ditto under the surname. Leave `dwelling`/ \
`house_num` blank when a new family shares the dwelling above (only a family number is written). On the page's \
first line, use `^` for a dwelling, house or family number that comes from the previous sheet.
- Ignore the census office's marks: check marks, tally marks, and the occupation code numbers written across \
the far-right columns 29-32 (e.g. "12 2 9 X", "15 5 4 3", often struck through with a slash). In a village \
those columns are nearly always blank, so leave `farm_schedule`, `veteran`, `blind` and `deaf_dumb` blank \
unless the enumerator clearly wrote an answer there.
- `line` is the line number printed on the form. A few sheets were filled in back to front, so a page called A \
can show lines 51-100; use the printed numbers as they are.
- `age`: as written. Infant ages stay as fractions, e.g. 8/12.
- Codes as written: sex M/F; race W, B, Mu, ...; marital S, M1, M2, Wd, D (M1 = first marriage, M2 = \
remarried); naturalization Na, Pa, Al; employer_class Emp, W, OA; out_of_work Yes/No; ownership O/R, F/M, \
H/F; veteran UA, UN, CA, CN. Literacy, school, blind and deaf_dumb are Yes/No (blank if the cell is blank).
- Birthplaces (columns 12-14): full names (Vermont, New Hampshire, Massachusetts, New York, Ireland, England, \
Scotland, Germany, ...). For people born abroad, the enumerator wrote the mother tongue after the country \
(e.g. "Canada French", "Can French", "Can Fr", "Canada English", "Germany German"; the language is \
sometimes written small above the country). Put the country in `birthplace` / \
`father_bp` / `mother_bp` and the language in `tongue` / `father_tongue` / `mother_tongue`. For Canada, write \
`Canada (Fr)` when the mother tongue is French and `Canada (Eng)` when it's English; plain Canada if it says \
neither. Blank if the page is blank, Unknown if it says unknown.
- `language` (column 17): English, or the language written there.
- `occupation` (column 18) and `industry` (column 19) in plain words as written (Weaver / Woolen mill, Laborer / Odd jobs, None).
- `uncertain` = 1 if any cell in the row is a guess, else 0. In `notes`, say which cell and the alternative \
reading. Never invent a value: leave unreadable cells blank and flag them."""

SCHEDULES = {
    1900: SimpleNamespace(
        year=1900,
        header=_1900_HEADER,
        guide=_1900_GUIDE,
        left_desc="street through immigration columns",
        right_desc="citizenship through home-ownership columns",
        census_day=(6, 1),  # month, day
    ),
    1910: SimpleNamespace(
        year=1910,
        header=_1910_HEADER,
        guide=_1910_GUIDE,
        left_desc="street through the language column, 1-17, and the start of occupation",
        right_desc="language through the last column, 17-32",
        census_day=(4, 15),
    ),
}


def get(year):
    if year not in SCHEDULES:
        raise SystemExit(f"no schedule for {year}; have {sorted(SCHEDULES)}")
    return SCHEDULES[year]
