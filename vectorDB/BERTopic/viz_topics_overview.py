# viz_topics_overview.py
import pandas as pd
import plotly.express as px

df = pd.read_csv("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTartifact/topic_info.csv")   # columns: Topic, Count, Name
df = df[df["Topic"]!=-1].sort_values("Count", ascending=False)

top_n = 70
fig = px.bar(
    df.head(top_n),
    x="Count", y="Name",
    orientation="h",
    title=f"Top {top_n} Topics by Count",
)
fig.update_layout(yaxis=dict(autorange="reversed"), height=900)
fig.write_html("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTopic/topics_overview.html", include_plotlyjs="cdn")
print("Wrote artifacts/topics_overview.html")


# viz_bertopic_interactive.py
from bertopic import BERTopic

topic_model = BERTopic.load("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTartifact/bertopic_model")

# 2.1 global topic map
fig_topics = topic_model.visualize_topics()
fig_topics.write_html("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTopic/vis_topics_map.html", include_plotlyjs="cdn")

# 2.2 inter-topic distances (UMAP projection)
fig_hmap = topic_model.visualize_hierarchy()
fig_hmap.write_html("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTopic/vis_hierarchy.html", include_plotlyjs="cdn")

# 2.3 per-topic top words (dropdown to switch topics)
fig_bars = topic_model.visualize_barchart(top_n_topics=70, n_words=10)  # adjust
fig_bars.write_html("/Users/Lorena/Developer/FlavorNet/vectorDB/BERTopic/vis_barchart.html", include_plotlyjs="cdn")

print("Wrote: vis_topics_map.html, vis_hierarchy.html, vis_barchart.html")