import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(
    page_title="Irish Property Prices",
    page_icon="🏠",
    layout="wide",
)

DATA = Path(__file__).parent / "data"


@st.cache_data
def load():
    d = {
        "summary":   pd.read_parquet(DATA / "area_summary.parquet"),
        "quarterly": pd.read_parquet(DATA / "area_quarterly.parquet"),
        "monthly":   pd.read_parquet(DATA / "area_monthly.parquet"),
        "sales":     pd.read_parquet(DATA / "recent_sales.parquet"),
        "county":    pd.read_parquet(DATA / "county_annual.parquet"),
        "national":  pd.read_parquet(DATA / "national_monthly.parquet"),
        "premium":   pd.read_parquet(DATA / "premium_annual.parquet"),
        "season":    pd.read_parquet(DATA / "seasonality.parquet"),
        "index":     pd.read_parquet(DATA / "cso_index.parquet"),
    }
    d["quarterly"]["quarter"] = pd.to_datetime(d["quarterly"]["quarter"])
    d["monthly"]["month"]     = pd.to_datetime(d["monthly"]["month"])
    d["national"]["month"]    = pd.to_datetime(d["national"]["month"])
    d["index"]["month"]       = pd.to_datetime(d["index"]["month"])
    d["sales"]["date"]        = pd.to_datetime(d["sales"]["date"])
    return d


d = load()


def eur(v, dp=0):
    if pd.isna(v):
        return "n/a"
    return f"€{v:,.{dp}f}"


# ── Sidebar navigation ───────────────────────────────────────────

st.sidebar.title("Irish Property Prices")
st.sidebar.caption(
    f"{len(d['summary'])} Eircode routing keys · "
    f"sales data to {d['national']['month'].max():%b %Y}"
)

page = st.sidebar.radio(
    "Page",
    ["Area explorer", "Compare areas", "National trends", "Method and limitations"],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.caption(
    "Area-level market statistics from the Property Price Register. "
    "**Not a property valuation tool** - see Method and limitations."
)


# ── Page 1: Area explorer ────────────────────────────────────────

if page == "Area explorer":
    st.title("Area explorer")

    s = d["summary"].sort_values(["county", "routing_key"])
    labels = {f"{r.routing_key} — {r.county}": r.routing_key for r in s.itertuples()}

    choice = st.selectbox("Routing key", list(labels), index=0)
    rk = labels[choice]
    row = s[s["routing_key"] == rk].iloc[0]

    st.caption(f"Based on {int(row.n_sales):,} sales since January 2024")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Median price", eur(row["median"]),
              f"{row.yoy_pct:+.1f}% YoY" if pd.notna(row.yoy_pct) else None)
    c2.metric("Typical range",
              f"{eur(row.p25/1000, 0)}k – {eur(row.p75/1000, 0)}k",
              help="Interquartile range: the middle 50% of sales")
    c3.metric("Price per sq m", eur(row.price_per_sqm),
              help="Area median price divided by mean dwelling size from BER records")
    c4.metric("New build share", f"{row.new_share*100:.0f}%",
              f"{row.new_premium_pct:+.0f}% premium" if pd.notna(row.new_premium_pct) else None)

    st.divider()

    left, right = st.columns([3, 2])

    with left:
        st.subheader("Price trend")
        q = d["quarterly"]
        area_q = q[(q["routing_key"] == rk) & (q["n"] >= 5)].copy()

        if len(area_q) < 2:
            st.warning("Not enough quarterly volume in this area to plot a trend.")
        else:
            nat = d["national"].copy()
            nat["quarter"] = nat["month"].dt.to_period("Q").dt.to_timestamp()
            nat_q = nat.groupby("quarter", as_index=False)["median"].median()

            merged = (area_q[["quarter", "median"]]
                      .rename(columns={"median": rk})
                      .merge(nat_q.rename(columns={"median": "National"}),
                             on="quarter", how="left")
                      .set_index("quarter"))

            st.line_chart(merged, height=300)
            st.caption(f"{rk} against the national median. "
                       "Quarters with fewer than five sales are omitted.")

    with right:
        st.subheader("Where sales fall")
        dist = pd.DataFrame(
            {"Price": [row.p10, row.p25, row["median"], row.p75, row.p90]},
            index=["1. 10th pct", "2. 25th", "3. Median", "4. 75th", "5. 90th pct"],
        )
        st.bar_chart(dist, height=300, horizontal=True)
        st.info(
            f"**80% of sales in {rk} fall between {eur(row.p10)} and {eur(row.p90)}.** "
            "This is a market range, not a valuation for any individual property."
        )

    st.divider()

    a, b = st.columns([2, 3])

    with a:
        st.subheader("Housing stock")
        st.write(
            f"- Mean dwelling size **{row.floor_area:,.0f} sq m**\n"
            f"- Median year built **{int(row.year_built)}**\n"
            f"- Rated A or B **{row.pct_ab*100:.0f}%**\n"
            f"- Mean BER rating **{row.ber_rating:,.0f}** (lower is more efficient)"
        )
        st.caption(
            "From SEAI BER records for this area. A BER is required only at sale "
            "or rental, so this describes assessed dwellings rather than all stock."
        )

    with b:
        st.subheader("Recent sales")
        sales = d["sales"]
        sales = sales[sales["routing_key"] == rk].sort_values("date", ascending=False)
        show = sales[["date", "address", "price_incl_vat", "property_type"]].copy()
        show.columns = ["Date", "Address", "Price", "Type"]
        show["Date"] = show["Date"].dt.strftime("%d %b %Y")
        show["Price"] = show["Price"].map(lambda v: eur(v))
        st.dataframe(show, hide_index=True, use_container_width=True, height=280)
        
# ── Page 2: Compare areas ────────────────────────────────────────

elif page == "Compare areas":
    st.title("Compare areas")

    s = d["summary"].sort_values(["county", "routing_key"])
    labels = {f"{r.routing_key} — {r.county}": r.routing_key for r in s.itertuples()}
    opts = list(labels)

    picks = st.multiselect(
        "Select two or three routing keys",
        opts,
        default=opts[:2],
        max_selections=3,
    )

    if len(picks) < 2:
        st.info("Select at least two areas to compare.")
    else:
        keys = [labels[p] for p in picks]
        rows = s[s["routing_key"].isin(keys)].set_index("routing_key").loc[keys]

        cols = st.columns(len(keys))
        for col, (rk, r) in zip(cols, rows.iterrows()):
            col.metric(f"{rk} — {r.county}", eur(r["median"]),
                       f"{r.yoy_pct:+.1f}% YoY" if pd.notna(r.yoy_pct) else None)

        st.divider()

        st.subheader("Price trend")
        q = d["quarterly"]
        trend = q[(q["routing_key"].isin(keys)) & (q["n"] >= 5)]
        wide = trend.pivot(index="quarter", columns="routing_key", values="median")
        st.line_chart(wide[keys], height=340)
        st.caption("Quarters with fewer than five sales are omitted.")

        st.divider()

        st.subheader("Side by side")
        table = pd.DataFrame({
            "Median price":        rows["median"].map(lambda v: eur(v)),
            "25th percentile":     rows["p25"].map(lambda v: eur(v)),
            "75th percentile":     rows["p75"].map(lambda v: eur(v)),
            "Price per sq m":      rows["price_per_sqm"].map(lambda v: eur(v)),
            "Year on year":        rows["yoy_pct"].map(lambda v: f"{v:+.1f}%" if pd.notna(v) else "n/a"),
            "Sales since 2024":    rows["n_sales"].map(lambda v: f"{int(v):,}"),
            "New build share":     rows["new_share"].map(lambda v: f"{v*100:.0f}%"),
            "Mean dwelling size":  rows["floor_area"].map(lambda v: f"{v:,.0f} sq m"),
            "Median year built":   rows["year_built"].map(lambda v: f"{int(v)}"),
            "Rated A or B":        rows["pct_ab"].map(lambda v: f"{v*100:.0f}%"),
        }).T
        table.columns = [f"{rk}" for rk in rows.index]
        st.dataframe(table, use_container_width=True)
        
# ── Page 3: National trends ──────────────────────────────────────

elif page == "National trends":
    st.title("National trends")

    st.subheader("Median price, 2010 to present")
    nat = d["national"].set_index("month")[["median", "mean"]]
    nat.columns = ["Median", "Mean"]
    st.line_chart(nat, height=320)
    st.caption(
        "Prices fell 31% to a trough of €149,796 in 2013, then rose 161% to "
        "€390,440 by 2026. The mean sits consistently above the median, and the "
        "gap widens over time as the upper end of the market pulls away."
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("County ranking")
        cty = d["county"]
        yr = st.slider("Year", int(cty["year"].min()), int(cty["year"].max()),
                       int(cty["year"].max()) - 1)
        sel = (cty[cty["year"] == yr]
               .sort_values("median", ascending=False)
               .reset_index(drop=True))
        sel["label"] = [f"{i+1:02d}. {c}" for i, c in enumerate(sel["county"])]
        sel = sel.set_index("label")[["median"]]
        sel.columns = ["Median price"]
        st.bar_chart(sel, height=520, horizontal=True)

    with right:
        st.subheader("Dublin against the rest")
        idx = d["index"].set_index("month")[["dublin", "ex_dublin"]]
        idx.columns = ["Dublin", "Excluding Dublin"]
        st.line_chart(idx[idx.index >= "2010-01-01"], height=250)
        st.caption(
            "CSO Residential Property Price Index. Since 2021 the ex-Dublin "
            "index has risen 57.7% against Dublin's 41.1%."
        )

        st.subheader("New build premium")
        prem = d["premium"].copy()
        prem["year"] = prem["year"].astype(str)
        prem = prem.set_index("year")[["premium_pct"]]
        prem.columns = ["Premium %"]
        st.line_chart(prem, height=230)
        st.caption(
            "New builds command a premium over second-hand. Negligible through "
            "2014, above 50% from 2016 to 2020, compressing to 27% by 2026 as "
            "construction output recovered."
        )

    st.divider()

    st.subheader("Seasonality")
    a, b = st.columns(2)

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seas = d["season"].copy()
    seas["name"] = [f"{i:02d} {months[i-1]}" for i in seas["month_num"]]

    with a:
        vol = seas.set_index("name")[["n"]]
        vol.columns = ["Sales"]
        st.bar_chart(vol, height=260)
        st.caption("December runs 41% above the average month, January 29% below.")

    with b:
        rel = seas.set_index("name")[["rel_price"]].copy()
        rel["rel_price"] = (rel["rel_price"] - 1) * 100
        rel.columns = ["% above/below year median"]
        st.bar_chart(rel, height=260)
        st.caption(
            "Price relative to each year's median, which removes the trend. "
            "February is cheapest at 0.95, October dearest at 1.03 - a spread "
            "of 7.6%. Volume and price seasonality are decoupled."
        )
        
        
# ── Page 4: Method and limitations ───────────────────────────────

elif page == "Method and limitations":
    st.title("Method and limitations")

    st.markdown("""
This application reports **area-level market statistics**. It does not estimate
the value of individual properties, and the analysis below explains why that is
not possible from Irish public data.
    """)

    st.divider()

    st.header("Why there is no valuation tool")

    c1, c2 = st.columns([2, 3])

    with c1:
        var = pd.DataFrame(
            {"Share of variation": [38.9, 61.1]},
            index=["Between areas", "Within areas"],
        )
        st.bar_chart(var, height=260, horizontal=True)

    with c2:
        st.markdown("""
Decomposing the variation in sale prices shows that **38.9% occurs between
Eircode routing keys and 61.1% occurs within them**.

In other words, most of what determines a price is the property itself - its
size, condition, bedroom count, garden, aspect, whether it needs work - rather
than the area it sits in.

The public data contains none of those attributes. A four-bedroom detached house
and a one-bedroom apartment on the same street are, to any model built on these
sources, identical.
        """)

    st.subheader("Model results")

    res = pd.DataFrame({
        "Model": ["Routing key median", "Ridge regression", "LightGBM",
                  "Perfect area knowledge"],
        "Median error": ["25.6%", "25.5%", "25.4%", "25.1%"],
        "Within 10%": ["21.2%", "21.0%", "21.3%", "—"],
        "Median error (€)": ["€92,496", "€92,090", "€91,185", "—"],
    })
    st.dataframe(res, hide_index=True, use_container_width=True)

    st.markdown("""
Three modelling approaches were tested against a naive baseline of predicting
each area's median. **None beat it meaningfully.** All sit within 0.3 percentage
points of the ceiling achievable with perfect knowledge of every area and no
property detail.

Prediction intervals from quantile regression are well calibrated, covering
80.3% of actual prices against an 80% target - but span **113% of the predicted
value**. A property estimated at €350,000 carries a range of roughly €180,000 to
€560,000. Honest, but not a valuation.
    """)

    st.divider()

    st.header("The data constraint")

    st.markdown("""
The constraint is legal rather than technical.

The **Property Price Register** records actual sale prices with addresses. The
**SEAI BER register** records dwelling characteristics - floor area, dwelling
type, year built, energy rating. Joining them at property level would provide
exactly the features needed.

A BER assessment includes the property address and MPRN, which makes it personal
data under GDPR. The public research extract removes both. The `SA_Code` field
that would have given CSO Small Area geography is present in the schema but
**entirely null across all 1,430,031 records**.

Access to the full BER data file is restricted under S.I. No. 243/2012 to the
assessor who carried out the assessment, an assessor performing a subsequent
one, or the building owner.

This is a privacy protection working as intended.
    """)

    st.divider()

    st.header("Data preparation")

    with st.expander("Cleaning decisions"):
        st.markdown("""
Starting from 799,067 sales, **750,660 were retained**.

- **40,721 removed** as not full market price - transfers between related
  parties and similar non-arms-length transactions
- **7,686 removed** by price bounds of €20,000 to €2,000,000. This scopes the
  data to individual dwellings: the upper tail contains genuine arms-length
  sales of apartment blocks and development sites, the largest being €388m
- **VAT adjustment of 13.5%** applied to 140,374 new builds, which are filed
  excluding VAT. Without this their prices are systematically understated
- **Irish-language category duplicates** harmonised - 49 sales across five
  distinct strings describing two underlying categories
        """)

    with st.expander("Data quality findings"):
        st.markdown("""
**The BER floor area columns are inverted relative to their names.**
`GroundFloorArea(sq m)` contains total dwelling floor area and `FloorArea`
contains the ground floor footprint. The ratio between them tracks storey count
almost exactly - 1.00 for single-storey, 1.89 for two-storey, 2.34 for
three-storey - and apartments show a footprint of zero while retaining a total
area. Taking the schema at face value would produce systematically wrong sizes.

**Eircode coverage changes sharply in 2021**, from under 1% through 2020 to 51%
in 2021 and 74-77% thereafter. Analysis requiring routing keys uses the 2021
onward window.

**The county field contains data entry errors.** 611 sales are filed against a
county accounting for under 1% of their routing key's transactions - a
Blessington, Co. Wicklow address filed under Westmeath, a Clane address under
Clare rather than Kildare. In each case the address and Eircode agree and
contradict the county field.

**Two placeholder Eircodes** were found - `A123456` appearing 156 times against
unrelated addresses nationwide, and `A00AA00`.
        """)

    with st.expander("Price indexing"):
        st.markdown("""
All prices are expressed in June 2026 money using the CSO Residential Property
Price Index, applied **separately for Dublin and the rest of the country**.

Since 2021 the ex-Dublin index rose 57.7% against Dublin's 41.1% - a gap of 16.6
percentage points. Using the national series would over-adjust Dublin sales and
under-adjust everywhere else.

The adjustment reduces the spread in annual medians from 36% to 3.9%.
        """)

    st.divider()

    st.header("What this data does support")

    st.markdown("""
- Price trends over time, nationally and by area, from 2010 to present
- Geographic comparison at routing key level, where variation reaches 2.34 to 1
  within Dublin alone
- New build premium analysis - a genuine 25% within comparable areas
- Seasonality in both transaction volume and price
- Price per square metre at area level, spanning 5.3 to 1 from Dublin 6 to
  Donegal
    """)

    st.divider()

    st.caption(
        "Sources: Property Price Register, SEAI National BER Research Tool, "
        "CSO Residential Property Price Index (table HPM09). "
        "Full analysis at github.com/DavidHeffernan94/IrishPropertyPrices"
    )