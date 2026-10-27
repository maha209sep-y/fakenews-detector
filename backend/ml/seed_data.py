"""
Small built-in seed dataset so the project runs out of the box.

IMPORTANT: this is only a demo dataset (a few dozen hand-written examples).
For real accuracy, download a proper dataset (see README) and put it in data/.
Label: 1 = fake / misleading, 0 = real / credible
"""

FAKE = [
    "SHOCKING: Doctors HATE this one weird trick that cures cancer overnight, big pharma is hiding it from you!!!",
    "BREAKING!!! Government secretly putting mind control chemicals in tap water, whistleblower reveals everything",
    "You won't believe what this celebrity did, the media doesn't want you to see this explosive truth",
    "Scientists confirm the moon landing was staged in a Hollywood studio, leaked documents prove it",
    "Miracle fruit melts belly fat in 3 days, nutritionists are furious and trying to ban this video",
    "URGENT: Share this message with 10 people or your phone will stop working tomorrow, official warning",
    "Secret elite cabal controls world economy and is planning to microchip every citizen by next year",
    "Vaccines contain tracking nanobots, insider from the lab exposes the shocking cover up",
    "Aliens have made contact with world leaders but the news is being suppressed by the deep state",
    "Drinking bleach mixed with lemon juice protects you from all viruses, secret doctors club reveals",
    "Famous politician arrested last night in massive scandal, mainstream media refuses to report it!!!",
    "100% proven: 5G towers are spreading disease and the telecom companies know it, wake up people",
    "This simple home remedy replaces all medicines, hospitals do not want you to know this secret",
    "Bank will close all accounts tomorrow, withdraw your money NOW, forwarded as received from a friend",
    "Exposed: the election was rigged by hacked machines, thousands of anonymous patriots confirm it",
    "Chemtrails are being sprayed to make the population obedient, pilot breaks silence in shocking video",
    "Free iPhone giveaway! Click this link now and enter your bank details to claim your prize today",
    "Man lives to 200 years by eating only one vegetable, scientists baffled and speechless",
    "Hidden truth about the pandemic: it was planned years ago by billionaires to control the world",
    "Breaking: famous actor dead at 40 in tragic accident, share to pay respects (rumor spreading online)",
    "Government to ban all cash from next Monday, secret memo leaked, panic spreads across the country",
    "Eating this common spice daily completely reverses diabetes, doctors shocked, pharma lobby furious",
    "Astonishing leaked video proves everything you were taught in school is a lie, the elites are terrified",
    "Miracle cure suppressed for decades: one pill ends all diseases forever, they tried to silence the inventor",
    "WARNING: new law will let police enter your house without any reason, share before they delete this post",
    "Scientist who discovered free energy machine found dead, oil companies behind the murder, say insiders",
    "Hot singles in your area are waiting, you will not believe number 7, doctors can't explain it",
    "Whole country shocked as president secretly replaced by a body double, anonymous source says",
]

REAL = [
    "The central bank held interest rates steady on Wednesday, citing moderating inflation and a stable labour market.",
    "Researchers at the university published a peer-reviewed study in a medical journal on the effects of regular exercise on heart health.",
    "The city council voted 7-2 to approve the new budget, which allocates additional funding to public transport and schools.",
    "Officials said the new bridge will open to traffic next month after the completion of final safety inspections.",
    "The national statistics office reported that unemployment fell to 4.8 percent in the third quarter, in line with analyst forecasts.",
    "The health ministry announced a vaccination drive for seasonal influenza beginning next week at all district hospitals.",
    "Heavy rainfall caused flooding in several low-lying districts, and the disaster response team evacuated about 2,000 residents, authorities said.",
    "The company reported quarterly revenue of 3.2 billion dollars, up 6 percent from a year earlier, according to its earnings statement.",
    "The national cricket team won the series 3-1 after a strong batting performance in the final match, the board said.",
    "The Supreme Court heard arguments on Tuesday in a case concerning data protection and is expected to deliver its ruling later this year.",
    "Scientists using the space telescope have identified a new exoplanet orbiting a nearby star, according to a paper published in a journal.",
    "The education department released the results of the board examinations, with the overall pass percentage rising slightly this year.",
    "The transport authority said that metro services will run on a revised schedule during the festival weekend to manage crowds.",
    "Police arrested two suspects in connection with the robbery after reviewing surveillance footage, a spokesperson told reporters.",
    "The finance minister presented the annual budget in parliament, outlining plans for infrastructure spending and tax reform.",
    "A report by the World Health Organization found that global life expectancy has recovered following the pandemic years.",
    "The airline announced it will launch three new international routes next spring, subject to regulatory approval.",
    "Engineers completed repairs on the power grid and electricity was restored to most affected neighbourhoods by evening, the utility said.",
    "The environment agency released data showing that air quality improved in major cities during the monsoon season.",
    "Local farmers received higher minimum support prices for wheat this season, the agriculture ministry confirmed in a statement.",
    "The university announced a new scholarship program for students from rural areas, with applications opening in January.",
    "Stock markets closed slightly higher on Friday as investors weighed corporate earnings and central bank commentary.",
    "The film festival opened on Thursday with screenings from more than 40 countries, organisers said at a press conference.",
    "The ministry of electronics said new guidelines on online safety will be published for public consultation next month.",
    "According to the census bureau, the population of the state grew by 1.2 percent over the past year.",
    "Doctors at the hospital performed a successful kidney transplant, and the patient is recovering well, a hospital spokesperson said.",
    "The prime minister met the visiting delegation on Monday to discuss trade cooperation and regional security, an official statement said.",
]

SEED_ROWS = [(t, 1) for t in FAKE] + [(t, 0) for t in REAL]