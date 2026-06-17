# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import google.auth
from typing import Literal

from pydantic import BaseModel
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.workflow import Workflow, Event, node
from google.adk.apps import App

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

class ClassificationOutput(BaseModel):
    category: Literal["shipping", "unrelated"]

@node
def save_query(node_input):
    # Extract text from input if it is a Content object
    text = str(node_input)
    if hasattr(node_input, "parts") and node_input.parts:
        text = node_input.parts[0].text
    elif isinstance(node_input, str):
        text = node_input
        
    return Event(output=node_input, state={"original_query_text": text})

classifier_agent = LlmAgent(
    name="classifier",
    model="gemini-flash-latest",
    instruction="Classify the user's query into one of two categories: 'shipping' (rates, tracking, delivery, returns) or 'unrelated'.",
    output_schema=ClassificationOutput,
)

@node
def route_query(ctx: Context, node_input: ClassificationOutput):
    original_query_text = ctx.state.get("original_query_text", "")
    if node_input.category == "shipping":
        return Event(output=original_query_text, route="shipping")
    return Event(output=None, route="unrelated")

shipping_faq = LlmAgent(
    name="shipping_faq",
    model="gemini-flash-latest",
    instruction="You are a shipping company FAQ agent. Answer questions about rates, tracking, delivery, and returns.",
)

@node
def decline_query(node_input):
    return "I am sorry, but I can only assist with shipping-related questions."

workflow = Workflow(
    name="customer_support_workflow",
    edges=[
        ("START", save_query),
        (save_query, classifier_agent),
        (classifier_agent, route_query),
        (route_query, shipping_faq, "shipping"),
        (route_query, decline_query, "unrelated"),
    ],
)

app = App(
    root_agent=workflow,
    name="app",
)
