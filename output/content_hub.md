
## ✏️ Title: Example Domain
- Source: example.com (manual)
- URL: https://example.com
- Fetched: 2026-02-23T17:44

URL Source: https://example.com/

Published Time: Wed, 18 Feb 2026 05:34:44 GMT

Warning: This is a cached snapshot of the original page, consider retry with caching opt-out.

Markdown Content:
This domain is for use in documentation examples without needing permission. Avoid use in operations.

[Learn more](https://iana.org/domains/example)

---

## ✏️ Title: Things we learned about LLMs in 2024
- Source: simonwillison.net (manual)
- URL: https://simonwillison.net/2024/Dec/31/llms-in-2024/
- Fetched: 2026-02-25T19:16

URL Source: https://simonwillison.net/2024/Dec/31/llms-in-2024/

Markdown Content:
31st December 2024

A _lot_ has happened in the world of Large Language Models over the course of 2024. Here’s a review of things we figured out about the field in the past twelve months, plus my attempt at identifying key themes and pivotal moments.

This is a sequel to [my review of 2023](https://simonwillison.net/2023/Dec/31/ai-in-2023/).

In this article:

*   [The GPT-4 barrier was comprehensively broken](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-gpt-4-barrier-was-comprehensively-broken)
*   [Some of those GPT-4 models run on my laptop](https://simonwillison.net/2024/Dec/31/llms-in-2024/#some-of-those-gpt-4-models-run-on-my-laptop)
*   [LLM prices crashed, thanks to competition and increased efficiency](https://simonwillison.net/2024/Dec/31/llms-in-2024/#llm-prices-crashed-thanks-to-competition-and-increased-efficiency)
*   [Multimodal vision is common, audio and video are starting to emerge](https://simonwillison.net/2024/Dec/31/llms-in-2024/#multimodal-vision-is-common-audio-and-video-are-starting-to-emerge)
*   [Voice and live camera mode are science fiction come to life](https://simonwillison.net/2024/Dec/31/llms-in-2024/#voice-and-live-camera-mode-are-science-fiction-come-to-life)
*   [Prompt driven app generation is a commodity already](https://simonwillison.net/2024/Dec/31/llms-in-2024/#prompt-driven-app-generation-is-a-commodity-already)
*   [Universal access to the best models lasted for just a few short months](https://simonwillison.net/2024/Dec/31/llms-in-2024/#universal-access-to-the-best-models-lasted-for-just-a-few-short-months)
*   [“Agents” still haven’t really happened yet](https://simonwillison.net/2024/Dec/31/llms-in-2024/#-agents-still-haven-t-really-happened-yet)
*   [Evals really matter](https://simonwillison.net/2024/Dec/31/llms-in-2024/#evals-really-matter)
*   [Apple Intelligence is bad, Apple’s MLX library is excellent](https://simonwillison.net/2024/Dec/31/llms-in-2024/#apple-intelligence-is-bad-apple-s-mlx-library-is-excellent)
*   [The rise of inference-scaling “reasoning” models](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-rise-of-inference-scaling-reasoning-models)
*   [Was the best currently available LLM trained in China for less than $6m?](https://simonwillison.net/2024/Dec/31/llms-in-2024/#was-the-best-currently-available-llm-trained-in-china-for-less-than-6m-)
*   [The environmental impact got better](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-environmental-impact-got-better)
*   [The environmental impact got much, much worse](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-environmental-impact-got-much-much-worse)
*   [The year of slop](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-year-of-slop)
*   [Synthetic training data works great](https://simonwillison.net/2024/Dec/31/llms-in-2024/#synthetic-training-data-works-great)
*   [LLMs somehow got even harder to use](https://simonwillison.net/2024/Dec/31/llms-in-2024/#llms-somehow-got-even-harder-to-use)
*   [Knowledge is incredibly unevenly distributed](https://simonwillison.net/2024/Dec/31/llms-in-2024/#knowledge-is-incredibly-unevenly-distributed)
*   [LLMs need better criticism](https://simonwillison.net/2024/Dec/31/llms-in-2024/#llms-need-better-criticism)
*   [Everything tagged “llms” on my blog in 2024](https://simonwillison.net/2024/Dec/31/llms-in-2024/#everything-tagged-llms-on-my-blog-in-2024)

#### The GPT-4 barrier was comprehensively broken[#](https://simonwillison.net/2024/Dec/31/llms-in-2024/#the-gpt-4-barrier-was-comprehensively-broken)

In my December 2023 review I wrote about how [We don’t yet know how to build GPT-4](https://simonwillison.net/2023/Dec/31/ai-in-2023/#cant-build-gpt4)—OpenAI’s best model was almost a year old at that point, yet no other AI lab had produced anything better. What did OpenAI know that the rest of us didn’t?

I’m relieved that this has changed completely in the past twelve months. 18 organizations now have models on the [Chatbot Arena Leaderboard](https://lmarena.ai/?leaderboard) that rank higher than the original GPT-4 from March 2023 (`GPT-4-0314` on the board)—70 models in total.

![Image 1: Screenshot of a comparison table showing AI model rankings. Table headers: Rank (UB), Rank (StyleCtrl), Model, Arena Score, 95% CI, Votes, Organization, License. Shows 12 models including GLM-4-0520, Llama-3-70B-Instruct, Gemini-1.5-Flash-8B-Exp-0827, with rankings, scores, and licensing details. Models range from rank 52-69 with Arena scores between 1186-1207.](https://static.simonwillison.net/static/2024/arena-dec-2024.jpg)

The earliest of those was **Google’s Gemini 1.5 Pro**, released in February. In addition to producing GPT-4 level outputs, it introduced several brand new capabilities to the field—most notably its 1 million (and then later 2 million) token input context length, and the ability to input video.

I wrote about this at the time in [The killer app of Gemini Pro 1.5 is video](https://simonwillison.net/2024/Feb/21/gemini-pro-video/), which earned me a short appearance [as a talking head](https://www.youtube.com/watch?v=XEzRZ35urlk&t=606s) in the Google I/O opening keynote in May.

Gemini 1.5 Pro also illustrated one of the key themes of 2024: **increased context lengths**. Last year most models accepted 4,096 or 8,192 tokens, with the notable exception of Claude 2.1 which [accepted 200,000](https://www.anthropic.com/news/claude-2-1). Today every serious provider has a 100,000+ token model, and Google’s Gemini series accepts up to 2 million.

Longer inputs dramatically increase the scope of problems that can be solved with an LLM: you can now throw in an entire book and ask questions about its contents, but more importantly you can feed in a _lot_ of example code to help the model correctly solve a coding problem. LLM use-cases that involve long inputs are far more interesting to me than short prompts that rely purely on the information already baked into the model weights. Many of my [tools](https://simonwillison.net/tags/tools/) were built using this pattern.

Getting back to models that beat GPT-4: Anthropic’s Claude 3 series [launched in March](https://simonwillison.net/2024/Mar/4/claude-3/), and Claude 3 Opus quickly became my new favourite daily-driver. They upped the ante even more in June with [the launch of Claude 3.5 Sonnet](https://simonwillison.net/2024/Jun/20/claude-35-sonnet/)—a model that is still my favourite six months later (though it got a significant upgrade [on October 22](https://www.anthropic.com/news/3-5-models-and-computer-use), confusingly keeping the same 3.5 version number. Anthropic fans have since taken to calling it Claude 3.6).

Then there’s the rest. If you browse [the Chatbot Arena leaderboard](https://lmarena.ai/?leaderboard) today—still the most useful single place to get [a vibes-based evaluation](https://simonwillison.net/2024/Jul/14/pycon/#pycon-2024.016.jpeg) of models—you’ll see that GPT-4-0314 has fallen to around 70th place. The 18 organizations with higher scoring models are Google, OpenAI, Alibaba, Anthropic, Meta, Reka AI, 01 AI, Amazon, Cohere, DeepSeek, Nvidia, Mistral, NexusFlow, Zhipu AI, xAI, AI21 Labs, Princeton and Tencent.

Training a GPT-4 beating model was a huge deal in 2023. In 2024 it’s an achievement that isn’t even particularly notable, though I personally still celebrate any time a new organization joins that list.

#### Some of those GPT-4 models run on my laptop[#](https://simonwillison.net/2024/Dec/31/llms-in-2024/#some-of-those-gpt-4-models-run-on-my-laptop)

My personal laptop is a 64GB M2 MacBook Pro from 2023. It’s a powerful machine, but it’s also nearly two years old now—and crucially it’s the same laptop I’ve been using ever since I first ran an LLM on my computer back in March 2023 (see [Large language models are having their Stable Diffusion moment](https://simonwillison.net/2023/Mar/11/llama/)).

That same laptop that could just about run a GPT-3-class model in March last year has now run multiple GPT-4 class models! Some of my notes on that:

*   [Qwen2.5-Coder-32B is an LLM that can code well that runs on my Mac](https://simonwillison.net/2024/Nov/12/qwen25-coder/) talks about Qwen2.5-Coder-32B in November—an Apache 2.0 licensed model!
*   [I can now run a GPT-4 class model on my laptop](https://simonwillison.net/2024/Dec/9/llama-33-70b/) talks about running Meta’s Llama 3.3 70B (released in December)

This remains astonishing to me. I thought a model with the capabilities and output quality of GPT-4 needed a datacenter class server with one or more $40,000+ GPUs.

These models take up enough of my 64GB of RAM that I don’t run them often—they don’t leave much room for anything else.

The fact that they run at all is a testament to the incredible training and inference performance gains that we’ve figured out over the past year. It turns out there was a _lot_ of low-hanging fruit to be harvested in terms of model efficiency. I expect there’s still more to come.

Meta’s Llama 3.2 models deserve a special mention. They may not be GPT-4 class, but at 1B and 3B sizes they punch _massively_ above their weight. I run Llama 3.2 3B on my iPhone using the free [MLC Chat iOS app](https://apps.apple.com/us/app/mlc-chat/id6448482937) and it’s a shockingly capable model for its tiny (<2GB) size. Try firing it up and asking it for “a plot outline of a Netflix Christmas movie where a data journalist falls in love with a local ceramacist”. Here’s what I got, at a respectable 20 tokens per second:

![Image 2: MLC Chat: Llama - [System] Ready to chat. a plot outline of a Netflix Christmas movie where a data journalist falls in love with a local ceramacist. Show as Markdown is turned on. Here's a plot outline for a Netflix Christmas movie: Title: "Love in the Clay" Plot Outline: We meet our protagonist, JESSICA, a data journalist who has just returned to her hometown of Will

---

## ✏️ Large language model
- Source: en.wikipedia.org (manual)
- URL: https://en.wikipedia.org/wiki/Large_language_model
- Fetched: 2026-02-25T19:18

URL Source: https://en.wikipedia.org/wiki/Large_language_model

Published Time: 2023-03-09T15:43:17Z

Markdown Content:
A **large language model** (**LLM**) is a [language model](https://en.wikipedia.org/wiki/Language_model "Language model") trained with [self-supervised](https://en.wikipedia.org/wiki/Self-supervised_learning "Self-supervised learning")[machine learning](https://en.wikipedia.org/wiki/Machine_learning "Machine learning") on a vast amount of text, designed for [natural language processing](https://en.wikipedia.org/wiki/Natural_language_processing "Natural language processing") tasks, especially [language generation](https://en.wikipedia.org/wiki/Language_generation "Language generation").[[1]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-bhaa-1)[[2]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-few-shot-learners-2) The largest and most capable LLMs are [generative pre-trained transformers](https://en.wikipedia.org/wiki/Generative_pre-trained_transformer "Generative pre-trained transformer") (GPTs) that provide the core capabilities of modern [chatbots](https://en.wikipedia.org/wiki/Chatbot "Chatbot"). LLMs can be [fine-tuned](https://en.wikipedia.org/wiki/Fine-tuning_(deep_learning) "Fine-tuning (deep learning)") for specific tasks or guided by [prompt engineering](https://en.wikipedia.org/wiki/Prompt_engineering "Prompt engineering").[[3]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-few-shot-learners2-3) These models acquire [predictive power](https://en.wikipedia.org/wiki/Predictive_learning "Predictive learning") regarding [syntax](https://en.wikipedia.org/wiki/Syntax "Syntax"), [semantics](https://en.wikipedia.org/wiki/Semantics "Semantics"), and [ontologies](https://en.wikipedia.org/wiki/Ontology_(information_science) "Ontology (information science)")[[4]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-4) inherent in human [language corpora](https://en.wikipedia.org/wiki/Text_corpus "Text corpus"), but they also inherit inaccuracies and [biases](https://en.wikipedia.org/wiki/Algorithmic_bias "Algorithmic bias") present in the [data](https://en.wikipedia.org/wiki/Training,_validation,_and_test_data_sets "Training, validation, and test data sets") they are trained on.[[5]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-Manning-2022-5)

They consist of billions to trillions of [parameters](https://en.wikipedia.org/wiki/Parameter#Artificial_intelligence "Parameter") and operate as general-purpose sequence models, generating, summarizing, translating, and reasoning over text. LLMs represent a significant new technology in their ability to generalize across tasks with minimal task-specific supervision, enabling capabilities like [conversational agents](https://en.wikipedia.org/wiki/Conversational_agent "Conversational agent"), [code generation](https://en.wikipedia.org/wiki/Automatic_programming "Automatic programming"), [knowledge retrieval](https://en.wikipedia.org/wiki/Information_retrieval "Information retrieval"), and [automated reasoning](https://en.wikipedia.org/wiki/Automated_reasoning "Automated reasoning") that previously required bespoke systems.[[6]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-scaling-laws-6)

LLMs evolved from earlier [statistical](https://en.wikipedia.org/wiki/Statistical_model "Statistical model") and [recurrent neural network](https://en.wikipedia.org/wiki/Recurrent_neural_network "Recurrent neural network") approaches to language modeling. The [transformer architecture](https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture) "Transformer (deep learning architecture)"), introduced in 2017, replaced recurrence with [self-attention](https://en.wikipedia.org/wiki/Attention_(machine_learning) "Attention (machine learning)"), allowing efficient [parallelization](https://en.wikipedia.org/wiki/Parallel_computing "Parallel computing"), longer context handling, and scalable training on unprecedented data volumes.[[7]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-7) This innovation enabled models like [GPT](https://en.wikipedia.org/wiki/GPT_(language_model) "GPT (language model)"), [BERT](https://en.wikipedia.org/wiki/BERT_(language_model) "BERT (language model)"), and their successors, which demonstrated [emergent behaviors](https://en.wikipedia.org/wiki/Emergence "Emergence") at scale, such as [few-shot learning](https://en.wikipedia.org/wiki/Prompt_engineering "Prompt engineering") and compositional reasoning.[[8]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-8)

[Reinforcement learning](https://en.wikipedia.org/wiki/Reinforcement_learning "Reinforcement learning"), particularly [policy gradient algorithms](https://en.wikipedia.org/wiki/Policy_gradient_method "Policy gradient method"), has been adapted to [fine-tune](https://en.wikipedia.org/wiki/Fine-tuning_(deep_learning) "Fine-tuning (deep learning)") LLMs for desired behaviors beyond raw next-token prediction.[[9]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-9)[Reinforcement learning from human feedback](https://en.wikipedia.org/wiki/Reinforcement_learning_from_human_feedback "Reinforcement learning from human feedback") (RLHF) applies these methods to optimize a policy, the LLM's output distribution, against reward signals derived from human or automated preference judgments.[[10]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-10) This has been critical for aligning model outputs with user expectations, improving factuality, reducing harmful responses, and enhancing task performance.

[Benchmark](https://en.wikipedia.org/wiki/Language_model_benchmark "Language model benchmark") evaluations for LLMs have evolved from narrow linguistic assessments toward comprehensive, [multi-task](https://en.wikipedia.org/wiki/Multi-task_learning "Multi-task learning") evaluations measuring [reasoning](https://en.wikipedia.org/wiki/Reasoning_model "Reasoning model"), [factual accuracy](https://en.wikipedia.org/wiki/Accuracy_and_precision "Accuracy and precision"), [alignment](https://en.wikipedia.org/wiki/AI_alignment "AI alignment"), and [safety](https://en.wikipedia.org/wiki/AI_safety "AI safety").[[11]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-11)[[12]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-12)[Hill climbing](https://en.wikipedia.org/wiki/Hill_climbing "Hill climbing"), iteratively optimizing models against benchmarks, has emerged as a dominant strategy, producing rapid incremental performance gains but raising concerns of [overfitting](https://en.wikipedia.org/wiki/Overfitting "Overfitting") to benchmarks rather than achieving genuine [generalization](https://en.wikipedia.org/wiki/Generalization_(machine_learning) "Generalization (machine learning)") or robust capability improvements.[[13]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-13)

[![Image 1](https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/The_number_of_publications_about_Large_Language_Models_by_year.png/250px-The_number_of_publications_about_Large_Language_Models_by_year.png)](https://en.wikipedia.org/wiki/File:The_number_of_publications_about_Large_Language_Models_by_year.png)

The number of publications about large language models by year grouped by publication types

[![Image 2](https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Trends_in_AI_training_FLOP_over_time_%282010-2025%29.svg/250px-Trends_in_AI_training_FLOP_over_time_%282010-2025%29.svg.png)](https://en.wikipedia.org/wiki/File:Trends_in_AI_training_FLOP_over_time_(2010-2025).svg)

The training compute of notable large models in FLOPs vs publication date over the period 2010–2024. For overall notable models (top left), frontier models (top right), top language models (bottom left) and top models within leading companies (bottom right). The majority of these models are language models.

[![Image 3](https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Large-scale_AI_training_compute_%28FLOP%29_vs_Publication_date_%282017-2024%29.svg/250px-Large-scale_AI_training_compute_%28FLOP%29_vs_Publication_date_%282017-2024%29.svg.png)](https://en.wikipedia.org/wiki/File:Large-scale_AI_training_compute_(FLOP)_vs_Publication_date_(2017-2024).svg)

The training compute of notable large AI models in FLOPs vs publication date over the period 2017–2024. The majority of large models are language models or multimodal models with language capacity.

Before the emergence of transformer-based models in 2017, some [language models](https://en.wikipedia.org/wiki/Language_model "Language model") were considered large relative to the computational and data constraints of their time. In the early 1990s, [IBM](https://en.wikipedia.org/wiki/IBM "IBM")'s statistical models pioneered [word alignment](https://en.wikipedia.org/wiki/Bitext_word_alignment "Bitext word alignment") techniques for machine translation, laying the groundwork for [corpus-based language modeling](https://en.wikipedia.org/wiki/Construction_grammar "Construction grammar"). In 2001, a smoothed [_n_-gram model](https://en.wikipedia.org/wiki/Word_n-gram_language_model "Word n-gram language model"), such as those employing [Kneser–Ney smoothing](https://en.wikipedia.org/wiki/Kneser%E2%80%93Ney_smoothing "Kneser–Ney smoothing"), trained on 300 million words, achieved state-of-the-art [perplexity](https://en.wikipedia.org/wiki/Perplexity "Perplexity") on benchmark tests.[[14]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-14) During the 2000s, with the rise of widespread internet access, researchers began compiling massive text datasets from the web ("web as corpus"[[15]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-15)) to train statistical language models.[[16]](https://en.wikipedia.org/wiki/Large_language_model#cite_note-16)[[17]](https://en.wikipedia.org/wiki/Large_language_model#cite_note

---
