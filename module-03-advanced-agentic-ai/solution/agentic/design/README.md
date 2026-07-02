Your design architecture goes in this folder

Incoming ticket + metadata
          |
          v
  Validate / load or create ticket
          |
          v
  Recall user preferences
          |
          v
   Classifier Agent
   category + urgency
   confidence + risk
          |
    +-----+------------------+
    |                        |
 high risk / low         normal case
 confidence                  |
    |                        v
    |                 Resolver Agent
    |                 |     |      |
    |                 |     |      +--> customer/account tools
    |                 |     +---------> semantic KB retrieval
    |                 +---------------> proposed action
    |                                      |
    |                               human approval interrupt
    |                                  |          |
    |                               approve      deny
    |                                  |          |
    +--------------------------+       v          |
                               | execute action   |
                               v                  v
                        Escalation Agent <--------+
                               |
                               v
                 Persist response, status, history
                               |
                               v
                    Update preference memory