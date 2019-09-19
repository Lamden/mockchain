supply = Variable()
balances = Hash(default_value=0)

@export
def transfer(amount, to):
    sender = ctx.caller

    balance = balances[sender]

    assert balance >= amount, 'Current balance {} from sender {} is less than amount {}.'.format(
        balance,
        sender,
        amount
    )

    balances[sender] -= amount
    balances[to] += amount


@export
def balance_of(account):
    return balances[account]

@export
def total_supply():
    return supply.get()

@export
def allowance(owner, spender):
    return balances[owner, spender]

@export
def approve(amount, to):
    sender = ctx.caller
    balances[sender, to] += amount
    return balances[sender, to]

@export
def transfer_from(amount, to, main_account):
    sender = ctx.caller

    assert balances[main_account, sender] >= amount, 'Not enough coins approved to send! You have {} and are trying to spend {}'\
        .format(balances[main_account, sender], amount)
    assert balances[main_account] >= amount, 'Not enough coins to send!'

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount
