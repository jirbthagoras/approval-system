# Overview
Just a simple approval system written in Python and deployed using Lambda + API Gateway. This part is only the Backend, so there is no Frontend and you must test using Postman.

## Steps
- Create VPC
- Adjusts the Security
- Create DB Instance
- Deploy Python code to Lambda
- Create and adjust the API Gateway
- Make SNS Topic and subscription
- Create the State Machine
- Test using postman.

## Technical Details
Create all services using 'lks' prefix, ex: lks-vpc

### VPC Networking
Just create using the default process, 2 public and private subnet. Make sure you have a NAT Gateway configured. 

### Security
There is only 1 things you need to concern about:
- Make sure the RDS only receives traffic from the Lambda Function. You have 2 options, figure it yourself!

### DB Instance
To create a DB Instance in Academy Account, make sure you set it to sandbox mode. We will use MariaDB engine for now, set the username to: admin, and password: SnapanCCMenangLKSNasional. Make sure you've created a subnet group before! Drop this RDS into the private subnets and make sure it uses your newly created Security Group.

### Lambdas
There is 5 lambda functions and each of them will have the same Environment Variables except lks_notify_email and lks_send_signal.

- lks_create_approval, lambda function to create a approval. The approval status will be set to pending in creation.
- lks_get_approval, lambda function to get all approvals and their status.
- lks_notify_email, used for publishig SNS topic to Subscriber.
- lks_send_signal, send a signal to the Step Function.
- lks_update_status, update the approval status to the decision.

### API Gateway
You must configure a API Gateway REST API And set this routes and integrate it with the lambdas you've created before:
- POST /approval -> lks_create_approval
- GET /approval -> lks_get_approval
- GET /approval/signal/{id} -> lks_send_signal

Don't forget to activate CORS!

### SNS Topic and Subscription
You must create a topic named ApprovalTopic, and for the subscriber, set it into 3 subscriber with different Subscription Filter Policy. As you can see in the code, the message will have a MessageAttribute named Type and the value will be depends on the sent signal. This is the Subscription Filter Policy:

- First subscriber, Type must be: BUY. Subscriber will decides approval status of BUY Type
- Second subscriber, Type must be: SALE. Subscriber will decides approval status of SALE Type
- Third subscriber, Type must be: REPORT. Will receives report SNS regarding the Rejection of Approvals

### State Machine
The important part of the State Machine is the waitForTaskToken attribute, which will BLOCKS the current Node and waiting for the sendSuccessTask signal. Node that have this waitForTaskToken attribute will receives a tasToken state, accessible via: $states.context.Task.Token for JSONata. The TaskToken needs to be accessed at the first Node to ensure correctness of the flow.

### Test
First you will create approval via the API. And then check the subscriber email, and finally there is option to reject or accept. Finally check the status by fetching GET /approval