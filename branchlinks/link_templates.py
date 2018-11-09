FACEBOOK_APP_ONLY = {
    "$3p": "a_facebook",
    "~secondary_ad_format": "App Install Ads",
    "~advertising_partner_name": "Facebook",
    "$one_time_use": "false",
    "~branch_ad_format": "App Only",
    "~channel": "Facebook",
    "~feature": "paid advertising"
}


FACEBOOK_CROSS_PLATFORM = {

    "$3p": "a_facebook",
    "~advertising_partner_name": "Facebook",
    "$one_time_use": "false",
    "~branch_ad_format": "Cross-Platform Display",
    "~channel": "Facebook",
    "~feature": "paid advertising"
}

GOOGLE_CROSS_PLATFORM = {
  "$android_passive_deepview": "false",
  "$3p": "a_google_adwords",
  "~advertising_partner_name": "Google AdWords",
  "$ios_passive_deepview": "false",
  "~feature": "paid advertising",
  "$desktop_deepview": "false",
  "$one_time_use": "false",
  "~branch_ad_format": "Cross-Platform Search",
  "~channel": "Google AdWords",
  "$ios_deepview": "false",
  "$android_deepview": "false",
  "~campaign_id": "{campaignid}",
  "gclid": "{gclid}",
  "lpurl": "{lpurl}",
  "~ad_set_id": "{adgroupid}",
  "~keyword": "{keyword}",
  "~placement": "{placement}",
  "$always_deeplink": "false"
}

TEMPLATE_DICT = {'GOOGLE_CROSS_PLATFORM': GOOGLE_CROSS_PLATFORM,
                 'FACEBOOK_CROSS_PLATFORM': FACEBOOK_CROSS_PLATFORM,
                 'FACEBOOK_APP_ONLY': FACEBOOK_APP_ONLY
}