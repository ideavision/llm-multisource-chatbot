import os

#####
# Payserai Slack Bot Configs
#####
PAYSERAI_BOT_NUM_RETRIES = int(os.environ.get("PAYSERAI_BOT_NUM_RETRIES", "5"))
PAYSERAI_BOT_ANSWER_GENERATION_TIMEOUT = int(
    os.environ.get("PAYSERAI_BOT_ANSWER_GENERATION_TIMEOUT", "90")
)
# Number of docs to display in "Reference Documents"
PAYSERAI_BOT_NUM_DOCS_TO_DISPLAY = int(
    os.environ.get("PAYSERAI_BOT_NUM_DOCS_TO_DISPLAY", "5")
)
# If the LLM fails to answer, Payserai can still show the "Reference Documents"
PAYSERAI_BOT_DISABLE_DOCS_ONLY_ANSWER = os.environ.get(
    "PAYSERAI_BOT_DISABLE_DOCS_ONLY_ANSWER", ""
).lower() not in ["false", ""]
# When Payserai is considering a message, what emoji does it react with
PAYSERAI_REACT_EMOJI = os.environ.get("PAYSERAI_REACT_EMOJI") or "eyes"
# Should PayseraiBot send an apology message if it's not able to find an answer
# That way the user isn't confused as to why PayseraiBot reacted but then said nothing
# Off by default to be less intrusive (don't want to give a notif that just says we couldnt help)

# Mostly for debugging purposes but it's for explaining what went wrong
# if PayseraiBot couldn't find an answer
PAYSERAI_BOT_DISPLAY_ERROR_MSGS = os.environ.get(
    "PAYSERAI_BOT_DISPLAY_ERROR_MSGS", ""
).lower() not in [
    "false",
    "",
]
# Default is only respond in channels that are included by a slack config set in the UI
PAYSERAI_BOT_RESPOND_EVERY_CHANNEL = (
    os.environ.get("PAYSERAI_BOT_RESPOND_EVERY_CHANNEL", "").lower() == "true"
)
# Auto detect query options like time cutoff or heavily favor recently updated docs
DISABLE_PAYSERAI_BOT_FILTER_DETECT = (
    os.environ.get("DISABLE_PAYSERAI_BOT_FILTER_DETECT", "").lower() == "true"
)
# Add a second LLM call post Answer to verify if the Answer is valid
# Throws out answers that don't directly or fully answer the user query
# This is the default for all PayseraiBot channels unless the channel is configured individually
# Set/unset by "Hide Non Answers"
ENABLE_PAYSERAIBOT_REFLEXION = (
    os.environ.get("ENABLE_PAYSERAIBOT_REFLEXION", "").lower() == "true"
)
# Currently not support chain of thought, probably will add back later
PAYSERAI_BOT_DISABLE_COT = True
