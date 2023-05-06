#### Environment variables (2) ####

#### AWS_ACCOUNT_NUMBER	123456789
#### RETENTION_DAYS	7

import boto3
import collections
import datetime
import os
import time

ec = boto3.client('ec2')

def lambda_handler(event, context):

# This funaction used to create manual AMI backup with tags, please check delete on date on AMI once it is created.
# It will backup for instances who has tag - Manual_Backup

    accountNumber = os.environ['AWS_ACCOUNT_NUMBER']
    retentionDays = int(os.environ['RETENTION_DAYS'])

    reservations = ec.describe_instances(
        Filters=[
            {'Name': 'tag:Manual_Backup', 'Values': ['True']}
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print ("Found %d instances that need backing up" % len(instances))

    to_tag = collections.defaultdict(list)
    amiList = []
    
    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
        except IndexError:
            retention_days = retentionDays
    
            create_time = datetime.datetime.now()
            create_fmt = create_time.strftime('%Y-%m-%d-%H-%M-%S')

            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    amiName = tag['Value']
                    break

            AMIid = ec.create_image(InstanceId=instance['InstanceId'], Name= amiName + " " + instance['InstanceId'] + " " + create_fmt, Description="Created by Manual_AMI_Backup function for " + instance['InstanceId'] + " on " + create_fmt, NoReboot=True, DryRun=False)
            print(AMIid['ImageId'])
            
            time.sleep(10)
            
            snapshots = ec.describe_snapshots(
                DryRun=False,
                OwnerIds=[
                    accountNumber
                ],
                Filters=[
                    {
                        'Name': 'description',
                        'Values': [
                            '*'+AMIid['ImageId']+'*'
                        ]
                    }
                ]
            ).get(
                'Snapshots', []
            )
           
            tag_resources = []
            
            tag_resources.append(AMIid['ImageId'])
            
            for snapshot in snapshots:
                print (snapshot['SnapshotId'])
                tag_resources.append(snapshot['SnapshotId'])
                
            
            response = ec.create_tags(
                Resources=tag_resources,
                Tags=instance['Tags']
            )

            to_tag[retention_days].append(AMIid['ImageId'])
            amiList.append(AMIid['ImageId'])
            print ("Retaining AMI %s of instance %s for %d days" % (
                AMIid['ImageId'],
                instance['InstanceId'],
                retention_days,
            ))

    for retention_days in to_tag.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%m-%d-%Y')
        print ("Will delete %d AMIs on %s" % (len(to_tag[retention_days]), delete_fmt))

        ec.create_tags(
            Resources=to_tag[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
                {'Key': 'Backup', 'Value': 'True'}
            ]
        )

    snapshotMaster = []
    time.sleep(5)
    print (amiList)
    for ami in amiList:
        print (ami)
        snapshots = ec.describe_snapshots(
            DryRun=False,
            OwnerIds=[
                accountNumber
            ],
            Filters=[
                {
                    'Name': 'description',
                    'Values': [
                        '*'+ami+'*'
                    ]
                }
            ]
        ).get(
            'Snapshots', []
        )
        print ("****************")

        for snapshot in snapshots:
            print (snapshot['SnapshotId'])
            ec.create_tags(
                Resources=[snapshot['SnapshotId']],
                Tags=[
                    {'Key': 'DeleteOn', 'Value': delete_fmt},
                    {'Key': 'Backup', 'Value': 'True'}
                ]
            )
