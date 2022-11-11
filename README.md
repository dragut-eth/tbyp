# tbyp
A research project that explores what blockchain technologies can bring to micro-blogging

TBYP
Take Back Your Privacy
Think Before You Post

Test this project on https://tbyp.herokuapp.com/

ERC-20 Token can used as a self moderation tools
Rules:
- First time user => +100 Token
- Create a new profile => -50 Token
- Upvote or Downvote => +0.1 Token
- Follow a user => Give 1 Token to user followed
- Post => -1 Token + -1 Token per tags : Stake 0.5 Token per followers (min. 0.5 Token)
- Edit Post => -1 Token
- Reward after 24h if Upvote - Downvote positif => Stake back +10%
- If Upvote - Downvote negatif after 24h => Lose Stake, post get removed from feeds 