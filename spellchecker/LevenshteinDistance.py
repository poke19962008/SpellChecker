def getInitialState(lenStartW, lenEndW):
    dp = [[0 for x in range(lenStartW+1)] for x in range(lenEndW+1)]
    dp[0] = [x for x in range(lenStartW+1)]
    for row in range(lenEndW+1):
        dp[row][0] = row

    return dp

def compute(start, end):
    lenStartW = len(start)
    lenEndW = len(end)
    dp = getInitialState(lenStartW, lenEndW)

    for j in range(1, lenStartW+1):
        for i in range(1, lenEndW+1):
            replaceCost = 0
            if start[j-1] != end[i-1]:
                replaceCost = 1

            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+replaceCost)

    return dp[lenEndW][lenStartW]
